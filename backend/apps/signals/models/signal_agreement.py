import uuid

from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class SignalAgreementMatrix(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="signal_agreement",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="signal_agreements"
    )
    signal_stances = models.JSONField(default=dict)
    agreements = models.JSONField(default=list)
    conflicts = models.JSONField(default=list)
    agreement_ratio = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("analysis_run_id", "version"),
                name="uq_signal_agreement_run_version",
            )
        ]
