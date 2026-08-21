from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class PortfolioConstructionOutput(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="portfolio_construction",
    )
    portfolio_state = models.ForeignKey(
        "risk_compliance.PortfolioState",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="construction_outputs",
    )
    methodology = models.CharField(max_length=60)
    target_allocations = models.JSONField(default=dict)
    current_allocations = models.JSONField(default=dict)
    constraints = models.JSONField(default=dict)
    expected_metrics = models.JSONField(default=dict)
    rebalance_required = models.BooleanField(default=False)
    rebalance_trades = models.JSONField(default=list)
