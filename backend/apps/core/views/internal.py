"""Authenticated endpoints used by Cloud Tasks and Cloud Scheduler."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, Final

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from config.task_backend import dispatch_task

logger = logging.getLogger(__name__)

ALLOWED_TASKS: Final = frozenset(
    {
        "apps.core.tasks.health_check",
        "apps.data_ingestion.tasks.ingest_enabled_sources",
        "apps.data_ingestion.tasks.ingest_source",
        "apps.orchestrator.tasks.extract_signal_domain",
        "apps.orchestrator.tasks.finalize_data_preparation",
        "apps.orchestrator.tasks.ingest_analysis_category",
        "apps.orchestrator.tasks.resume_pm_decision",
        "apps.orchestrator.tasks.run_adversarial_review",
        "apps.orchestrator.tasks.run_compliance_check",
        "apps.orchestrator.tasks.run_conviction_scoring",
        "apps.orchestrator.tasks.run_full_pipeline",
        "apps.orchestrator.tasks.run_peer_analysis",
        "apps.orchestrator.tasks.run_pm_synthesis",
        "apps.orchestrator.tasks.run_portfolio_optimization",
        "apps.orchestrator.tasks.run_position_sizing",
        "apps.orchestrator.tasks.run_risk_validation",
        "apps.orchestrator.tasks.run_specialist_agent",
        "apps.orchestrator.tasks.signals_completed",
        "apps.orchestrator.tasks.specialists_completed",
        "apps.orchestrator.tasks.start_data_preparation",
        "apps.orchestrator.tasks.validate_canonical_data",
        "apps.portfolio.tasks.expire_pm_reviews",
        "apps.portfolio.tasks.monitor_catalysts",
        "apps.portfolio.tasks.monitor_exit_triggers",
        "apps.portfolio.tasks.track_recommendation_performance",
        "apps.signals.tasks.extract_technical_signals",
        "internal.execute_chain",
    }
)


def verify_internal_request(
    request: HttpRequest,
    *,
    audience: str,
    allowed_service_accounts: set[str],
) -> bool:
    """Validate a Google-signed OIDC token and its service-account identity."""
    if settings.INTERNAL_ENDPOINTS_ALLOW_UNAUTHENTICATED:
        return True
    if not audience or not allowed_service_accounts:
        logger.error("internal_auth.misconfigured")
        return False

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token:
        return False

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=audience.rstrip("/"),
        )
    except (ValueError, TypeError):
        logger.warning("internal_auth.invalid_token", exc_info=True)
        return False

    return bool(claims.get("email_verified") and claims.get("email") in allowed_service_accounts)


@method_decorator(csrf_exempt, name="dispatch")
class WorkerExecuteView(View):
    """Execute one explicitly allowed Celery task for Cloud Tasks."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> JsonResponse:
        if not verify_internal_request(
            request,
            audience=settings.CLOUD_RUN_WORKER_URL,
            allowed_service_accounts={settings.CLOUD_TASKS_SA_EMAIL},
        ):
            return JsonResponse({"error": "Unauthorized"}, status=401)
        if len(request.body) > settings.INTERNAL_TASK_MAX_BODY_BYTES:
            return JsonResponse({"error": "Task payload is too large"}, status=413)

        try:
            payload = json.loads(request.body)
            task_name = payload["task_name"]
            args = payload.get("args", [])
            kwargs = payload.get("kwargs", {})
            self._validate_payload(task_name, args, kwargs)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        cloud_task_name = request.headers.get("X-CloudTasks-TaskName", "")
        lock_key = f"cloud-task:running:{cloud_task_name}" if cloud_task_name else ""
        done_key = f"cloud-task:completed:{cloud_task_name}" if cloud_task_name else ""
        if done_key and cache.get(done_key):
            return JsonResponse({"status": "already_completed", "task": cloud_task_name})
        if lock_key and not cache.add(
            lock_key,
            "running",
            timeout=settings.INTERNAL_TASK_LOCK_TIMEOUT_SECONDS,
        ):
            return JsonResponse({"error": "Task execution is already in progress"}, status=429)

        try:
            self._execute_task(task_name, tuple(args), kwargs)
        except Exception as exc:
            if lock_key:
                cache.delete(lock_key)
            logger.exception(
                "cloud_tasks.execution_failed",
                extra={"task_name": task_name, "cloud_task_name": cloud_task_name},
            )
            return JsonResponse({"error": type(exc).__name__}, status=500)

        if done_key:
            cache.set(done_key, True, timeout=settings.INTERNAL_TASK_DEDUPLICATION_SECONDS)
            cache.delete(lock_key)
        return JsonResponse({"status": "completed"})

    @staticmethod
    def _validate_payload(task_name: Any, args: Any, kwargs: Any) -> None:
        if not isinstance(task_name, str) or task_name not in ALLOWED_TASKS:
            raise ValueError("Task is not allowed")
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise TypeError("args must be a list and kwargs must be an object")

    @staticmethod
    def _execute_task(task_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        if task_name == "internal.execute_chain":
            chain = kwargs.get("chain")
            if not isinstance(chain, list) or not 1 <= len(chain) <= 50:
                raise ValueError("chain must contain between 1 and 50 steps")
            results = []
            for step in chain:
                if not isinstance(step, dict):
                    raise TypeError("Every chain step must be an object")
                step_name = step.get("task_name")
                step_args = step.get("args", [])
                step_kwargs = step.get("kwargs", {})
                WorkerExecuteView._validate_payload(step_name, step_args, step_kwargs)
                if step_name == "internal.execute_chain":
                    raise ValueError("Nested task chains are not allowed")
                results.append(
                    WorkerExecuteView._execute_task(step_name, tuple(step_args), step_kwargs)
                )
            return results

        from config.celery import app

        task = app.tasks.get(task_name)
        if task is None:
            # Importing the task module registers all application tasks.
            module_name = task_name.rsplit(".", 1)[0]
            __import__(module_name)
            task = app.tasks.get(task_name)
        if task is None:
            raise LookupError(f"Registered task not found: {task_name}")
        return task.run(*args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class SchedulerDispatchView(View):
    """Fan out one consolidated Cloud Scheduler invocation to Cloud Tasks."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest, schedule_name: str) -> JsonResponse:
        if not verify_internal_request(
            request,
            audience=settings.CLOUD_RUN_BACKEND_URL,
            allowed_service_accounts={settings.CLOUD_SCHEDULER_SA_EMAIL},
        ):
            return JsonResponse({"error": "Unauthorized"}, status=401)

        handler = SCHEDULE_HANDLERS.get(schedule_name)
        if handler is None:
            return JsonResponse({"error": f"Unknown schedule: {schedule_name}"}, status=404)
        try:
            task_ids = handler()
        except Exception as exc:
            logger.exception("cloud_scheduler.dispatch_failed", extra={"schedule": schedule_name})
            return JsonResponse({"error": type(exc).__name__}, status=500)
        return JsonResponse({"status": "dispatched", "tasks": task_ids})


def _handle_market_data_hourly() -> list[str]:
    return [
        dispatch_task(
            "apps.data_ingestion.tasks.ingest_enabled_sources",
            kwargs={"categories": ["quote", "ohlcv", "news"]},
            queue="ingestion",
        )
    ]


def _handle_reference_data_daily() -> list[str]:
    return [
        dispatch_task(
            "apps.data_ingestion.tasks.ingest_enabled_sources",
            kwargs={
                "categories": [
                    "company_profile",
                    "financial_statement",
                    "filing",
                    "ownership",
                    "peer_group",
                    "macro",
                ]
            },
            queue="ingestion",
        )
    ]


def _handle_portfolio_monitors() -> list[str]:
    # One five-minute Scheduler job preserves the original mixed cadences while
    # staying within the three-job Always Free allowance.
    now = timezone.now()
    task_names = [
        "apps.portfolio.tasks.monitor_exit_triggers",
        "apps.portfolio.tasks.expire_pm_reviews",
    ]
    if now.minute == 0:
        task_names.append("apps.portfolio.tasks.monitor_catalysts")
    if now.hour == 2 and now.minute == 0:
        task_names.append("apps.portfolio.tasks.track_recommendation_performance")
    return [dispatch_task(task_name, queue="computation") for task_name in task_names]


SCHEDULE_HANDLERS: Final[dict[str, Callable[[], list[str]]]] = {
    "market-data-hourly": _handle_market_data_hourly,
    "reference-data-daily": _handle_reference_data_daily,
    "portfolio-monitors": _handle_portfolio_monitors,
}
