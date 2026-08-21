from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class ReviewRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class PMReviewRequest(TimeStampedModel):
    """Durable, optimistic-lock protected PM human-review lifecycle."""

    recommendation = models.OneToOneField(
        "portfolio.PMRecommendation",
        on_delete=models.CASCADE,
        related_name="review_request",
    )
    status = models.CharField(
        max_length=20,
        choices=ReviewRequestStatus.choices,
        default=ReviewRequestStatus.PENDING,
        db_index=True,
    )
    checkpoint_thread_id = models.CharField(max_length=255)
    expires_at = models.DateTimeField(db_index=True)
    lock_version = models.PositiveIntegerField(default=1)
    decision = models.CharField(
        max_length=20,
        choices=(("approve", "Approve"), ("reject", "Reject"), ("defer", "Defer")),
        blank=True,
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pm_review_decisions",
    )
    rationale = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        unique=True,
    )

    class Meta:
        indexes = [models.Index(fields=("status", "expires_at"))]

    @property
    def is_expired(self) -> bool:
        return self.status == ReviewRequestStatus.PENDING and self.expires_at <= timezone.now()
