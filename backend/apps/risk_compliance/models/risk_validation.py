from django.db import models

from apps.core.domain.enums import RiskDecision
from apps.core.models import TimeStampedModel, VersionedMixin


class RiskValidationResult(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="risk_validation",
    )
    decision = models.CharField(max_length=30, choices=RiskDecision.choices())
    passed = models.BooleanField(default=False)
    risk_metrics = models.JSONField(default=dict)
    breaches = models.JSONField(default=list)
    mitigations = models.JSONField(default=list)
    hedge_suggestions = models.JSONField(default=list)
    scenario_results = models.JSONField(default=dict)
    rationale = models.TextField()
    requires_escalation = models.BooleanField(default=False)
    rule_version = models.CharField(max_length=50, blank=True)
