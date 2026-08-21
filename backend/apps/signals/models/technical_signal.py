from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel, VersionedMixin


class TechnicalSignal(TimeStampedModel, ProvenanceMixin, VersionedMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="technical_signals"
    )
    signal_type = models.CharField(max_length=80, db_index=True)
    timeframe = models.CharField(max_length=20)
    observed_at = models.DateTimeField(db_index=True)
    value = models.FloatField(null=True, blank=True)
    direction = models.CharField(
        max_length=20,
        choices=(
            ("bullish", "Bullish"),
            ("bearish", "Bearish"),
            ("neutral", "Neutral"),
        ),
    )
    strength = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    parameters = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "ticker",
                    "signal_type",
                    "timeframe",
                    "observed_at",
                    "version",
                ),
                name="uq_technical_signal_observation",
            )
        ]
        indexes = [models.Index(fields=("ticker", "signal_type", "-observed_at"))]
