from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class PositionSizingRecommendation(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="sizing_recommendation",
    )
    methodology = models.CharField(max_length=60)
    portfolio_weight_pct = models.DecimalField(max_digits=10, decimal_places=6)
    num_shares = models.PositiveBigIntegerField(default=0)
    dollar_amount = models.DecimalField(max_digits=24, decimal_places=2)
    entry_tranches = models.PositiveSmallIntegerField(default=1)
    risk_budget_contribution = models.DecimalField(max_digits=12, decimal_places=8)
    incremental_risk = models.JSONField(default=dict)
    assumptions = models.JSONField(default=dict)
