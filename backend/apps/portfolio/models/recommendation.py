from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.domain.enums import ActionSignal, TimeHorizon
from apps.core.models import TimeStampedModel, VersionedMixin


class RecommendationStatus(models.TextChoices):
    PENDING_REVIEW = "pending_review", "Pending review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    DEFERRED = "deferred", "Deferred"


class PMRecommendation(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="recommendation",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker",
        on_delete=models.PROTECT,
        related_name="pm_recommendations",
    )
    action = models.CharField(max_length=20, choices=ActionSignal.choices())
    conviction = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(
        max_length=20,
        choices=RecommendationStatus.choices,
        default=RecommendationStatus.PENDING_REVIEW,
        db_index=True,
    )
    summary = models.TextField()
    rationale = models.TextField()
    expected_return = models.JSONField(default=dict)
    position_size = models.JSONField(default=dict)
    entry_plan = models.JSONField(default=list)
    exit_conditions = models.JSONField(default=dict)
    time_horizon = models.CharField(max_length=20, choices=TimeHorizon.choices())
    catalysts = models.JSONField(default=list)
    portfolio_fit = models.TextField()
    capital_allocation_guidance = models.TextField()
    conditions_precedent = models.JSONField(default=list)
    evidence = models.JSONField(default=list)
    assumptions = models.JSONField(default=list)
    limitations = models.JSONField(default=list)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_recommendations",
    )
    review_rationale = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=("ticker", "status", "-created_at"))]
