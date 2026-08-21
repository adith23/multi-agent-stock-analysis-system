"""Append-only audit trail for user, service, model, and agent actions."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.domain.exceptions import AuditImmutabilityError
from apps.core.models import UUIDModel
from apps.core.utils.hashing import content_hash


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    READ = "read", "Read"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    APPROVE = "approve", "Approve"
    REJECT = "reject", "Reject"
    OVERRIDE = "override", "Override"
    ESCALATE = "escalate", "Escalate"
    EXECUTE = "execute", "Execute"
    REQUEST = "request", "HTTP Request"
    ERROR = "error", "Error"


class AppendOnlyAuditQuerySet(models.QuerySet["AuditTrailRecord"]):
    def update(self, **kwargs: Any) -> int:
        raise AuditImmutabilityError("audit records are append-only")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise AuditImmutabilityError("audit records are append-only")


class AuditTrailRecord(UUIDModel):
    """Immutable event record satisfying FR-056 and NFR-011 through NFR-014."""

    occurred_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    actor_label = models.CharField(max_length=150, blank=True, editable=False)
    action = models.CharField(
        max_length=24,
        choices=AuditAction.choices,
        db_index=True,
        editable=False,
    )
    event_type = models.CharField(max_length=100, db_index=True, editable=False)
    resource_type = models.CharField(max_length=100, blank=True, db_index=True, editable=False)
    resource_id = models.CharField(max_length=255, blank=True, db_index=True, editable=False)
    request_id = models.CharField(max_length=64, blank=True, db_index=True, editable=False)
    method = models.CharField(max_length=10, blank=True, editable=False)
    path = models.CharField(max_length=512, blank=True, editable=False)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True, editable=False)
    user_agent = models.CharField(max_length=512, blank=True, editable=False)
    summary = models.TextField(blank=True, editable=False)
    metadata = models.JSONField(default=dict, blank=True, editable=False)
    previous_values = models.JSONField(default=dict, blank=True, editable=False)
    new_values = models.JSONField(default=dict, blank=True, editable=False)
    agent_version = models.CharField(max_length=50, blank=True, editable=False)
    model_version = models.CharField(max_length=50, blank=True, editable=False)
    prompt_version = models.CharField(max_length=50, blank=True, editable=False)
    event_hash = models.CharField(max_length=64, unique=True, editable=False)

    objects = AppendOnlyAuditQuerySet.as_manager()

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("resource_type", "resource_id", "-occurred_at")),
            models.Index(fields=("actor", "-occurred_at")),
            models.Index(fields=("event_type", "-occurred_at")),
        ]
        verbose_name = "audit trail record"
        verbose_name_plural = "audit trail records"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise AuditImmutabilityError("audit records are append-only")
        if not self.event_hash:
            self.event_hash = content_hash(
                {
                    "id": str(self.id),
                    "occurred_at": self.occurred_at,
                    "actor": str(self.actor_id or ""),
                    "action": self.action,
                    "event_type": self.event_type,
                    "resource_type": self.resource_type,
                    "resource_id": self.resource_id,
                    "request_id": self.request_id,
                    "metadata": self.metadata,
                    "previous_values": self.previous_values,
                    "new_values": self.new_values,
                }
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise AuditImmutabilityError("audit records are append-only")

    def __str__(self) -> str:
        return f"{self.occurred_at.isoformat()} {self.event_type}:{self.action}"
