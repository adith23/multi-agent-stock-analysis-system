from apps.core.tasks import health_check


def test_celery_health_task_runs_eagerly() -> None:
    result = health_check.delay()
    assert result.get() == {"status": "ok"}
