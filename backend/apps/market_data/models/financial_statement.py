from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel


class StatementType(models.TextChoices):
    INCOME = "income", "Income statement"
    BALANCE_SHEET = "balance_sheet", "Balance sheet"
    CASH_FLOW = "cash_flow", "Cash flow"
    METRICS = "metrics", "Financial metrics"


class FinancialStatement(TimeStampedModel, ProvenanceMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="financial_statements"
    )
    statement_type = models.CharField(max_length=30, choices=StatementType.choices)
    period_end = models.DateField(db_index=True)
    fiscal_year = models.PositiveSmallIntegerField()
    fiscal_quarter = models.PositiveSmallIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    accession_number = models.CharField(max_length=40, blank=True)
    values = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ticker", "statement_type", "period_end", "source_type"),
                name="uq_fin_stmt_period_source",
            )
        ]
        indexes = [models.Index(fields=("ticker", "statement_type", "-period_end"))]
