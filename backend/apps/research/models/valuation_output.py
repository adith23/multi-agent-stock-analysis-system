import uuid

from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class ValuationOutput(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="valuation_outputs"
    )
    methodology = models.CharField(max_length=80)
    currency = models.CharField(max_length=3, default="USD")
    bear_value = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    base_value = models.DecimalField(max_digits=24, decimal_places=8)
    bull_value = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    assumptions = models.JSONField(default=dict)
    sensitivities = models.JSONField(default=dict)
    evidence = models.JSONField(default=list)

    class Meta:
        indexes = [models.Index(fields=("ticker", "-created_at"))]
