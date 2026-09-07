from django.db import models

from apps.core.models import TimeStampedModel


class DataPreparationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    READY = "ready", "Ready"
    DEGRADED = "degraded", "Degraded"
    FAILED = "failed", "Failed"


class DataPreparationRun(TimeStampedModel):
    """Auditable data-readiness work performed for one analysis run."""

    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="data_preparation",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker",
        on_delete=models.PROTECT,
        related_name="data_preparations",
    )
    status = models.CharField(
        max_length=20,
        choices=DataPreparationStatus.choices,
        default=DataPreparationStatus.PENDING,
        db_index=True,
    )
    requested_categories = models.JSONField(default=list)
    plan = models.JSONField(default=dict)
    cache_hits = models.JSONField(default=list)
    source_attempts = models.JSONField(default=list)
    fallbacks = models.JSONField(default=list)
    category_results = models.JSONField(default=dict)
    selected_sources = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=("ticker", "status", "-created_at"))]

    def __str__(self) -> str:
        return f"Data preparation {self.analysis_run_id}: {self.status}"
