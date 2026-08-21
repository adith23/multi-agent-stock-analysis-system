from __future__ import annotations

from django.dispatch import receiver
from django_structlog.celery import signals

CELERY_CONTEXT_KEYS = frozenset({"request_id", "correlation_id", "user_id"})


@receiver(signals.modify_context_before_task_publish)
def retain_safe_celery_log_context(sender, signal, context, **kwargs) -> None:
    """Propagate only bounded, non-domain request metadata to Celery."""

    safe_context = {
        key: str(context[key])[:255] for key in CELERY_CONTEXT_KEYS if context.get(key) is not None
    }
    context.clear()
    context.update(safe_context)
