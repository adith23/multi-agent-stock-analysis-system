from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel


class CompanyProfile(TimeStampedModel, ProvenanceMixin):
    ticker = models.OneToOneField(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="profile"
    )
    legal_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(max_length=500, blank=True)
    headquarters_country = models.CharField(max_length=80, blank=True)
    market_cap = models.DecimalField(max_digits=24, decimal_places=4, null=True, blank=True)
    shares_outstanding = models.DecimalField(
        max_digits=24, decimal_places=4, null=True, blank=True
    )
    ipo_date = models.DateField(null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Profile: {self.ticker}"
