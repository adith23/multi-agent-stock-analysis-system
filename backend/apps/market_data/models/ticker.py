from django.db import models

from apps.core.models import TimeStampedModel


class SecurityType(models.TextChoices):
    EQUITY = "equity", "Equity"
    ETF = "etf", "ETF"
    FUND = "fund", "Fund"
    INDEX = "index", "Index"
    ADR = "adr", "ADR"
    OTHER = "other", "Other"


class TickerQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def for_symbol(self, symbol: str, exchange: str | None = None):
        query = self.filter(symbol=symbol.strip().upper())
        return query.filter(exchange=exchange.strip().upper()) if exchange else query


class Ticker(TimeStampedModel):
    """Security master entry; symbol uniqueness is scoped to an exchange."""

    symbol = models.CharField(max_length=32)
    exchange = models.CharField(max_length=32, default="US")
    name = models.CharField(max_length=255, blank=True)
    isin = models.CharField(max_length=12, blank=True, db_index=True)
    cusip = models.CharField(max_length=9, blank=True, db_index=True)
    currency = models.CharField(max_length=3, default="USD")
    security_type = models.CharField(
        max_length=20, choices=SecurityType.choices, default=SecurityType.EQUITY
    )
    sector = models.ForeignKey(
        "market_data.Sector",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickers",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    objects = TickerQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("symbol", "exchange"),
                name="uq_ticker_symbol_exchange",
            )
        ]
        indexes = [models.Index(fields=("symbol", "is_active"))]
        ordering = ("symbol", "exchange")

    def save(self, *args, **kwargs) -> None:
        self.symbol = self.symbol.strip().upper()
        self.exchange = self.exchange.strip().upper()
        self.currency = self.currency.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.symbol}:{self.exchange}"
