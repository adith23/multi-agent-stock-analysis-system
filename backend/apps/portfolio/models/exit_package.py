from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class ExitPackageStatus(models.TextChoices):
    PENDING = "pending", "Pending approval"
    ACTIVE = "active", "Active"
    TRIGGERED = "triggered", "Triggered"
    CLOSED = "closed", "Closed"


class ExitStrategyPackage(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="exit_package",
    )
    status = models.CharField(
        max_length=20,
        choices=ExitPackageStatus.choices,
        default=ExitPackageStatus.PENDING,
        db_index=True,
    )
    entry_price = models.DecimalField(max_digits=24, decimal_places=8)
    stop_loss_price = models.DecimalField(max_digits=24, decimal_places=8)
    stop_loss_pct = models.FloatField()
    profit_targets = models.JSONField(default=list)
    trailing_stop = models.JSONField(default=dict)
    thesis_invalidation_triggers = models.JSONField(default=list)
    time_based_review_date = models.DateTimeField()
    current_price = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    trigger_type = models.CharField(max_length=60, blank=True)
    trigger_details = models.JSONField(default=dict)
    triggered_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
