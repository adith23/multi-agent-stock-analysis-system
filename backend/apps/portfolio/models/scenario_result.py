from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class ScenarioAnalysisResult(TimeStampedModel, VersionedMixin):
    analysis_run = models.ForeignKey(
        "orchestrator.AnalysisRun",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scenario_results",
    )
    portfolio_state = models.ForeignKey(
        "risk_compliance.PortfolioState",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scenario_results",
    )
    name = models.CharField(max_length=255)
    scenario_type = models.CharField(max_length=50, default="user_defined")
    inputs = models.JSONField(default=dict)
    results = models.JSONField(default=dict)
    worst_impact = models.FloatField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scenario_analyses",
    )
