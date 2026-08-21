from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel


class InsiderTransaction(TimeStampedModel, ProvenanceMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="insider_transactions"
    )
    owner_name = models.CharField(max_length=255)
    owner_relationship = models.CharField(max_length=120, blank=True)
    transaction_date = models.DateField(db_index=True)
    transaction_code = models.CharField(max_length=20, blank=True)
    shares = models.DecimalField(max_digits=24, decimal_places=4, null=True, blank=True)
    price = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    value = models.DecimalField(max_digits=28, decimal_places=4, null=True, blank=True)
    is_direct_ownership = models.BooleanField(null=True)
    accession_number = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ticker", "content_hash", "source_type"),
                name="uq_insider_tx_hash_source",
            )
        ]
        indexes = [models.Index(fields=("ticker", "-transaction_date"))]
