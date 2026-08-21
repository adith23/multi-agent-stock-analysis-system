import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class CatalystRecord(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    run = models.ForeignKey(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="catalysts",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="catalysts"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    catalyst_type = models.CharField(max_length=60, db_index=True)
    expected_at = models.DateTimeField(null=True, blank=True, db_index=True)
    direction = models.CharField(
        max_length=20,
        choices=(("positive", "Positive"), ("negative", "Negative"), ("uncertain", "Uncertain")),
        default="uncertain",
    )
    probability = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    impact = models.CharField(max_length=30, blank=True)
    evidence = models.JSONField(default=list)
    is_active = models.BooleanField(default=True, db_index=True)
    is_thesis_critical = models.BooleanField(default=False)
    outcome_status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "Pending"),
            ("occurred", "Occurred"),
            ("failed", "Failed"),
            ("delayed", "Delayed"),
            ("cancelled", "Cancelled"),
        ),
        default="pending",
        db_index=True,
    )
    actual_at = models.DateTimeField(null=True, blank=True)
    outcome_notes = models.TextField(blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    alert_sent = models.BooleanField(default=False)
