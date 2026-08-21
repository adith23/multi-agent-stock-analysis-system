import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class BullBearDecisionMemo(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="decision_memo",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="decision_memos"
    )
    bull_case = models.TextField()
    bear_case = models.TextField()
    base_case = models.TextField()
    key_disagreements = models.JSONField(default=list)
    falsifiers = models.JSONField(default=list)
    evidence = models.JSONField(default=list)
    confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    weak_assumptions = models.JSONField(default=list)
    missing_evidence = models.JSONField(default=list)
    material_unknowns = models.JSONField(default=list)
    premortem = models.JSONField(default=list)
    debate_rounds = models.PositiveSmallIntegerField(default=1)
    output_snapshot = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("analysis_run_id", "version"),
                name="uq_decision_memo_run_version",
            )
        ]
