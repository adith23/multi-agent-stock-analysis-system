from django.conf import settings
from django.db import models

from apps.core.domain.enums import ComplianceDecision
from apps.core.models import TimeStampedModel, VersionedMixin


class ComplianceResult(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="compliance_result",
    )
    decision = models.CharField(max_length=30, choices=ComplianceDecision.choices())
    passed = models.BooleanField(default=False)
    restricted_list_match = models.BooleanField(default=False)
    checks = models.JSONField(default=list)
    violations = models.JSONField(default=list)
    approval_required = models.BooleanField(default=False)
    overridden = models.BooleanField(default=False)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="compliance_reviews",
    )
    review_rationale = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rule_version = models.CharField(max_length=50, blank=True)
