"""Dispatch application tasks through Celery or Google Cloud Tasks.

Celery remains the local-development backend.  Production uses Cloud Tasks to
send authenticated HTTP requests to the private Cloud Run worker service.
Google client libraries are imported lazily so local commands do not require
Google credentials.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from django.conf import settings

logger = logging.getLogger(__name__)

CELERY_BACKEND: Final = "celery"
CLOUD_TASKS_BACKEND: Final = "cloud_tasks"
SUPPORTED_BACKENDS: Final = frozenset({CELERY_BACKEND, CLOUD_TASKS_BACKEND})
QUEUE_MAP: Final = {
    "default": "default",
    "orchestrator": "orchestrator",
    "agents": "agents",
    "computation": "computation",
    "ingestion": "ingestion",
}


class TaskDispatchError(RuntimeError):
    """Raised when a task cannot be represented or dispatched safely."""


def dispatch_task(
    task_name: str,
    args: Sequence[Any] = (),
    kwargs: dict[str, Any] | None = None,
    queue: str = "default",
    countdown: int | None = None,
) -> str:
    """Dispatch a task and return its Celery or Cloud Tasks identifier."""
    backend = str(settings.TASK_BACKEND).casefold()
    if backend not in SUPPORTED_BACKENDS:
        raise TaskDispatchError(f"Unsupported task backend: {backend!r}")
    if queue not in QUEUE_MAP:
        raise TaskDispatchError(f"Unsupported task queue: {queue!r}")
    if countdown is not None and countdown < 0:
        raise TaskDispatchError("countdown must be greater than or equal to zero")

    task_kwargs = kwargs or {}
    if backend == CLOUD_TASKS_BACKEND:
        return _dispatch_cloud_task(task_name, tuple(args), task_kwargs, queue, countdown)
    return _dispatch_celery_task(task_name, tuple(args), task_kwargs, queue, countdown)


def _dispatch_celery_task(
    task_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    queue: str,
    countdown: int | None,
) -> str:
    from config.celery import app

    signature = app.signature(
        task_name,
        args=args,
        kwargs=kwargs,
        queue=queue,
    )
    result = signature.apply_async(countdown=countdown)
    return str(result.id)


def _dispatch_cloud_task(
    task_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    queue: str,
    countdown: int | None,
) -> str:
    _validate_cloud_tasks_settings()

    from google.cloud import tasks_v2
    from google.protobuf import duration_pb2, timestamp_pb2

    try:
        body = json.dumps(
            {"task_name": task_name, "args": list(args), "kwargs": kwargs},
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TaskDispatchError(f"Task payload is not JSON serializable: {task_name}") from exc

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_LOCATION,
        QUEUE_MAP[queue],
    )
    task: dict[str, Any] = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{settings.CLOUD_RUN_WORKER_URL.rstrip('/')}/api/internal/worker/execute/",
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": body,
            "oidc_token": {
                "service_account_email": settings.CLOUD_TASKS_SA_EMAIL,
                "audience": settings.CLOUD_RUN_WORKER_URL.rstrip("/"),
            },
        },
        # Cloud Tasks HTTP targets support a maximum 30-minute deadline.
        "dispatch_deadline": duration_pb2.Duration(
            seconds=settings.CLOUD_TASKS_DISPATCH_DEADLINE_SECONDS
        ),
    }
    if countdown:
        schedule_time = timestamp_pb2.Timestamp()
        schedule_time.FromDatetime(datetime.now(UTC) + timedelta(seconds=countdown))
        task["schedule_time"] = schedule_time

    response = client.create_task(parent=parent, task=task)
    logger.info(
        "cloud_tasks.dispatched",
        extra={
            "task_name": task_name,
            "queue": QUEUE_MAP[queue],
            "cloud_task_name": response.name,
        },
    )
    return str(response.name)


def dispatch_chain(task_sequence: Sequence[dict[str, Any]], queue: str = "default") -> str:
    """Dispatch a sequence through one Cloud Task or a native Celery chain."""
    if not task_sequence:
        raise TaskDispatchError("task_sequence must contain at least one task")
    for step in task_sequence:
        if not isinstance(step.get("task_name"), str):
            raise TaskDispatchError("Every chain step must define a task_name")

    if str(settings.TASK_BACKEND).casefold() == CLOUD_TASKS_BACKEND:
        return dispatch_task(
            "internal.execute_chain",
            kwargs={"chain": list(task_sequence)},
            queue=queue,
        )

    from celery import chain as celery_chain

    from config.celery import app

    signatures = [
        app.signature(
            step["task_name"],
            args=step.get("args", ()),
            kwargs=step.get("kwargs", {}),
        )
        for step in task_sequence
    ]
    result = celery_chain(*signatures).apply_async(queue=queue)
    return str(result.id)


def _validate_cloud_tasks_settings() -> None:
    required = (
        "GCP_PROJECT_ID",
        "GCP_LOCATION",
        "CLOUD_RUN_WORKER_URL",
        "CLOUD_TASKS_SA_EMAIL",
    )
    missing = [name for name in required if not getattr(settings, name, "")]
    if missing:
        raise TaskDispatchError(
            "Cloud Tasks configuration is incomplete: " + ", ".join(sorted(missing))
        )
    deadline = settings.CLOUD_TASKS_DISPATCH_DEADLINE_SECONDS
    if not 15 <= deadline <= 1800:
        raise TaskDispatchError(
            "CLOUD_TASKS_DISPATCH_DEADLINE_SECONDS must be between 15 and 1800"
        )
