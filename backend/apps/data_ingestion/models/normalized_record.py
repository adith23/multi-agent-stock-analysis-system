from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel
from apps.data_ingestion.domain.enums import DataCategory, IngestionStatus


class NormalizedRecordQuerySet(models.QuerySet):
    def accepted(self):
        return self.filter(status=IngestionStatus.ACCEPTED)

    def for_entity(self, identifier: str):
        return self.filter(entity_identifier=identifier.strip().upper())

    def latest_first(self):
        return self.order_by("-source_timestamp", "-created_at")


class NormalizedDataRecord(TimeStampedModel, ProvenanceMixin):
    raw_input = models.ForeignKey(
        "data_ingestion.RawInputObject",
        on_delete=models.PROTECT,
        related_name="normalized_records",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="normalized_records",
    )
    data_category = models.CharField(max_length=40, choices=DataCategory.choices, db_index=True)
    entity_identifier = models.CharField(max_length=120, blank=True, db_index=True)
    canonical_key = models.CharField(max_length=500, blank=True, db_index=True)
    normalized_payload = models.JSONField(default=dict)
    schema_version = models.CharField(max_length=30, default="1.0")
    language = models.CharField(max_length=10, default="en")
    similarity_hash = models.CharField(max_length=16, blank=True, db_index=True)
    lineage = models.JSONField(default=dict)
    quality_issues = models.JSONField(default=list, blank=True)
    quality_flags = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=IngestionStatus.choices, default=IngestionStatus.ACCEPTED
    )

    objects = NormalizedRecordQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_type", "data_category", "content_hash"),
                name="uq_normalized_source_category_hash",
            )
        ]
        indexes = [
            models.Index(fields=("entity_identifier", "data_category", "-source_timestamp")),
            models.Index(fields=("status", "-created_at")),
        ]
