import uuid

from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class PeerAnalysisReport(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="peer_report",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="peer_analysis_reports"
    )
    peer_group = models.ForeignKey(
        "market_data.PeerGroup",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analysis_reports",
    )
    comparison_dimensions = models.JSONField(default=dict)
    relative_ranking = models.JSONField(default=dict)
    differentiators = models.JSONField(default=list)
    summary = models.TextField()
    evidence = models.JSONField(default=list)
