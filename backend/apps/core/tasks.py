"""Foundation Celery tasks used for operational smoke checks."""

from __future__ import annotations

from celery import shared_task


@shared_task(name="apps.core.tasks.health_check", ignore_result=True)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
