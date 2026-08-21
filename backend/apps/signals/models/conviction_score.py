import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.domain.enums import ActionSignal
from apps.core.models import TimeStampedModel, VersionedMixin


class ConvictionScorePackage(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="conviction_score",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="conviction_scores"
    )
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    level = models.CharField(max_length=30)
    action_signal = models.CharField(
        max_length=20,
        choices=ActionSignal.choices(),
    )
    expected_return_low = models.FloatField(null=True, blank=True)
    expected_return_high = models.FloatField(null=True, blank=True)
    horizon_days = models.PositiveIntegerField(null=True, blank=True)
    component_scores = models.JSONField(default=dict)
    evidence = models.JSONField(default=list)
    caveats = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("analysis_run_id", "version"),
                name="uq_conviction_run_version",
            )
        ]
