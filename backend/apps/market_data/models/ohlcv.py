from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel


class BarInterval(models.TextChoices):
    MINUTE_1 = "1m", "1 minute"
    MINUTE_5 = "5m", "5 minutes"
    MINUTE_15 = "15m", "15 minutes"
    HOUR_1 = "1h", "1 hour"
    DAY_1 = "1d", "1 day"
    WEEK_1 = "1wk", "1 week"
    MONTH_1 = "1mo", "1 month"


class OHLCVQuerySet(models.QuerySet):
    def for_ticker(self, ticker):
        return self.filter(ticker=ticker)

    def between(self, start, end):
        return self.filter(timestamp__gte=start, timestamp__lte=end)

    def latest_first(self):
        return self.order_by("-timestamp")


class OHLCVBar(TimeStampedModel, ProvenanceMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="ohlcv_bars"
    )
    timestamp = models.DateTimeField(db_index=True)
    interval = models.CharField(
        max_length=8, choices=BarInterval.choices, default=BarInterval.DAY_1
    )
    open = models.DecimalField(max_digits=24, decimal_places=8, validators=[MinValueValidator(0)])
    high = models.DecimalField(max_digits=24, decimal_places=8, validators=[MinValueValidator(0)])
    low = models.DecimalField(max_digits=24, decimal_places=8, validators=[MinValueValidator(0)])
    close = models.DecimalField(max_digits=24, decimal_places=8, validators=[MinValueValidator(0)])
    adjusted_close = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    volume = models.DecimalField(
        max_digits=30, decimal_places=4, validators=[MinValueValidator(0)]
    )

    objects = OHLCVQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ticker", "timestamp", "interval", "source_type"),
                name="uq_ohlcv_ticker_time_interval_source",
            ),
            models.CheckConstraint(
                condition=models.Q(high__gte=models.F("low")),
                name="ck_ohlcv_high_gte_low",
            ),
        ]
        indexes = [models.Index(fields=("ticker", "interval", "-timestamp"))]
        ordering = ("ticker", "-timestamp")
