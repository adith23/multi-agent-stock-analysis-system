import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class SpecialistReport(TimeStampedModel, VersionedMixin):
    """Versioned evidence-first output from one specialist agent."""

    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    run = models.ForeignKey(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="specialist_reports",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="specialist_reports"
    )
    specialist_type = models.CharField(max_length=50, db_index=True)
    thesis = models.TextField()
    summary = models.TextField(blank=True)
    evidence = models.JSONField(default=list)
    assumptions = models.JSONField(default=list)
    limitations = models.JSONField(default=list)
    confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    stance = models.CharField(max_length=20, blank=True)
    input_references = models.JSONField(default=list)
    output_snapshot = models.JSONField(default=dict)
    generated_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("analysis_run_id", "specialist_type", "version"),
                name="uq_specialist_report_run_type_version",
            )
        ]
        indexes = [models.Index(fields=("ticker", "specialist_type", "-generated_at"))]
