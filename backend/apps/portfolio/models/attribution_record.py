from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class PerformanceAttributionRecord(TimeStampedModel, VersionedMixin):
    recommendation = models.ForeignKey(
        "portfolio.PMRecommendation",
        on_delete=models.CASCADE,
        related_name="performance_records",
    )
    measurement_period = models.CharField(max_length=30)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    entry_price = models.DecimalField(max_digits=24, decimal_places=8)
    exit_price = models.DecimalField(max_digits=24, decimal_places=8)
    realized_return = models.FloatField()
    benchmark_return = models.FloatField(default=0)
    excess_return = models.FloatField(default=0)
    hit = models.BooleanField()
    risk_adjusted_return = models.FloatField(null=True, blank=True)
    agent_attribution = models.JSONField(default=dict)
    signal_decay = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("recommendation", "measurement_period", "version"),
                name="uq_attribution_recommendation_period_version",
            )
        ]
