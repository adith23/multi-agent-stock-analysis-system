from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel


class NewsItem(TimeStampedModel, ProvenanceMixin):
    ticker = models.ForeignKey(
        "market_data.Ticker",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="news_items",
    )
    headline = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    url = models.URLField(max_length=1000, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    author = models.CharField(max_length=255, blank=True)
    published_at = models.DateTimeField(db_index=True)
    language = models.CharField(max_length=10, default="en")
    sentiment_score = models.FloatField(null=True, blank=True)
    categories = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("content_hash", "source_type"),
                name="uq_news_hash_source",
            )
        ]
        indexes = [models.Index(fields=("-published_at", "publisher"))]
