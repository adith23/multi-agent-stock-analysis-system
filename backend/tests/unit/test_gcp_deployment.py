from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.test import Client, override_settings

from config.secret_bundle import SecretBundleError, load_secret_bundle
from config.task_backend import TaskDispatchError, dispatch_task
from ml.model_loader import ModelArtifactError, get_model_path


@override_settings(TASK_BACKEND="celery")
@patch("config.celery.app.signature")
def test_dispatch_task_uses_celery_locally(build_signature: Mock) -> None:
    build_signature.return_value.apply_async.return_value = SimpleNamespace(id="celery-id")

    task_id = dispatch_task("apps.core.tasks.health_check", queue="default", countdown=5)

    assert task_id == "celery-id"
    build_signature.assert_called_once_with(
        "apps.core.tasks.health_check",
        args=(),
        kwargs={},
        queue="default",
    )
    build_signature.return_value.apply_async.assert_called_once_with(countdown=5)


@override_settings(TASK_BACKEND="unsupported")
def test_dispatch_task_rejects_unknown_backend() -> None:
    with pytest.raises(TaskDispatchError, match="Unsupported task backend"):
        dispatch_task("apps.core.tasks.health_check")


@override_settings(TASK_BACKEND="celery")
def test_dispatch_task_rejects_unknown_queue() -> None:
    with pytest.raises(TaskDispatchError, match="Unsupported task queue"):
        dispatch_task("apps.core.tasks.health_check", queue="typo")


@override_settings(INTERNAL_ENDPOINTS_ALLOW_UNAUTHENTICATED=False)
@pytest.mark.django_db
def test_worker_endpoint_requires_authentication() -> None:
    response = Client().post(
        "/api/internal/worker/execute/",
        data={"task_name": "apps.portfolio.tasks.expire_pm_reviews"},
        content_type="application/json",
    )

    assert response.status_code == 401


@override_settings(INTERNAL_ENDPOINTS_ALLOW_UNAUTHENTICATED=True)
@pytest.mark.django_db
def test_worker_endpoint_rejects_tasks_outside_allowlist() -> None:
    response = Client().post(
        "/api/internal/worker/execute/",
        data={"task_name": "os.system", "args": [], "kwargs": {}},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Task is not allowed"}


@override_settings(INTERNAL_ENDPOINTS_ALLOW_UNAUTHENTICATED=True)
@patch("apps.core.views.internal.WorkerExecuteView._execute_task")
@pytest.mark.django_db
def test_worker_endpoint_executes_allowed_task(execute_task: Mock) -> None:
    execute_task.return_value = {"expired": 0}

    response = Client().post(
        "/api/internal/worker/execute/",
        data={
            "task_name": "apps.portfolio.tasks.expire_pm_reviews",
            "args": [],
            "kwargs": {},
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    execute_task.assert_called_once_with(
        "apps.portfolio.tasks.expire_pm_reviews",
        (),
        {},
    )


@override_settings(INTERNAL_ENDPOINTS_ALLOW_UNAUTHENTICATED=True)
@patch("apps.core.views.internal.SCHEDULE_HANDLERS")
@pytest.mark.django_db
def test_scheduler_endpoint_dispatches_consolidated_schedule(handlers: Mock) -> None:
    handlers.get.return_value = lambda: ["task-1", "task-2"]

    response = Client().post(
        "/api/internal/scheduler/portfolio-monitors/",
        data={},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"status": "dispatched", "tasks": ["task-1", "task-2"]}


@override_settings(GCS_ML_MODELS_BUCKET="", ML_MODEL_CACHE_DIR="/tmp/models")
def test_model_loader_uses_local_artifact(tmp_path) -> None:
    artifact = tmp_path / "regime.joblib"
    artifact.write_bytes(b"model")

    with override_settings(ML_MODEL_DIR=str(tmp_path)):
        assert get_model_path("regime.joblib") == artifact


def test_model_loader_rejects_path_traversal() -> None:
    with pytest.raises(ModelArtifactError, match="safe relative"):
        get_model_path("../credentials.json")


def test_secret_bundle_loads_only_missing_allowed_values(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "explicit")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    load_secret_bundle('{"DATABASE_URL":"bundled","GOOGLE_API_KEY":"key"}')

    assert os.environ["DATABASE_URL"] == "explicit"
    assert os.environ["GOOGLE_API_KEY"] == "key"


def test_secret_bundle_rejects_unknown_keys() -> None:
    with pytest.raises(SecretBundleError, match="unsupported keys"):
        load_secret_bundle('{"DJANGO_DEBUG":"true"}')
