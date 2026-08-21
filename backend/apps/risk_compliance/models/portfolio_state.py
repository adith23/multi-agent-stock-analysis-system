from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class PortfolioState(TimeStampedModel, VersionedMixin):
    portfolio_code = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="portfolio_snapshots",
    )
    as_of = models.DateTimeField(db_index=True)
    base_currency = models.CharField(max_length=3, default="USD")
    total_value = models.DecimalField(max_digits=24, decimal_places=2)
    holdings = models.JSONField(default=list)
    weights = models.JSONField(default=dict)
    sector_exposures = models.JSONField(default=dict)
    factor_exposures = models.JSONField(default=dict)
    liquidity_metrics = models.JSONField(default=dict)
    risk_metrics = models.JSONField(default=dict)
    gross_leverage = models.FloatField(default=1.0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("portfolio_code", "as_of", "version"),
                name="uq_portfolio_snapshot_code_time_version",
            )
        ]
        indexes = [models.Index(fields=("portfolio_code", "-as_of"))]
