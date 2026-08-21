from django.db import models

from apps.core.models import TimeStampedModel
from apps.data_ingestion.domain.enums import DataCategory, IngestionStatus, SourceType


class RawInputObject(TimeStampedModel):
    """Immutable retained response received from an external source."""

    source_config = models.ForeignKey(
        "data_ingestion.DataSourceConfiguration",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="raw_inputs",
    )
    source_type = models.CharField(max_length=30, choices=SourceType.choices, db_index=True)
    data_category = models.CharField(max_length=40, choices=DataCategory.choices, db_index=True)
    external_id = models.CharField(max_length=255, blank=True)
    entity_identifier = models.CharField(max_length=120, blank=True, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    raw_text = models.TextField(blank=True)
    fetched_at = models.DateTimeField(db_index=True)
    source_timestamp = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=10, default="en")
    media_type = models.CharField(max_length=100, default="application/json")
    schema_version = models.CharField(max_length=30, default="raw")
    request_metadata = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=64, db_index=True)
    status = models.CharField(
        max_length=20, choices=IngestionStatus.choices, default=IngestionStatus.PENDING
    )
    error_message = models.TextField(blank=True)
    retention_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_type", "data_category", "content_hash"),
                name="uq_raw_source_category_hash",
            )
        ]
        indexes = [
            models.Index(fields=("entity_identifier", "data_category", "-fetched_at")),
            models.Index(fields=("status", "-fetched_at")),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            persisted = type(self).objects.only("raw_payload", "raw_text").get(pk=self.pk)
            if persisted.raw_payload != self.raw_payload or persisted.raw_text != self.raw_text:
                raise ValueError("Raw input payloads are immutable")
        super().save(*args, **kwargs)
