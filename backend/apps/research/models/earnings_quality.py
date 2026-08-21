import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class EarningsQualityReport(TimeStampedModel, VersionedMixin):
    analysis_run_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="earnings_quality_reports"
    )
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    accrual_metrics = models.JSONField(default=dict)
    cash_conversion_metrics = models.JSONField(default=dict)
    accounting_flags = models.JSONField(default=list)
    evidence = models.JSONField(default=list)
