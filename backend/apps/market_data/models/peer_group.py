from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class PeerGroup(TimeStampedModel, VersionedMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker", on_delete=models.CASCADE, related_name="owned_peer_groups"
    )
    peers = models.ManyToManyField("market_data.Ticker", related_name="peer_groups", blank=True)
    name = models.CharField(max_length=160)
    methodology = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ticker", "name", "version"),
                name="uq_peer_group_version",
            )
        ]
