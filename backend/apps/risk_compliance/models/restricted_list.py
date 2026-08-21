from django.db import models

from apps.core.models import AuditMixin, TimeStampedModel


class RestrictedSecurity(TimeStampedModel, AuditMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker",
        on_delete=models.CASCADE,
        related_name="restrictions",
    )
    reason = models.TextField()
    policy_reference = models.CharField(max_length=120, blank=True)
    effective_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=("ticker", "is_active", "-effective_at"))]
