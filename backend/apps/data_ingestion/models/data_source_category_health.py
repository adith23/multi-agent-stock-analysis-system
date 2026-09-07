from django.db import models

from apps.core.models import TimeStampedModel
from apps.data_ingestion.domain.enums import DataCategory


class DataSourceCategoryHealth(TimeStampedModel):
    """Health state for one data category exposed by a configured source."""

    source_config = models.ForeignKey(
        "data_ingestion.DataSourceConfiguration",
        on_delete=models.CASCADE,
        related_name="category_health",
    )
    data_category = models.CharField(max_length=40, choices=DataCategory.choices)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source_config", "data_category"),
                name="unique_source_category_health",
            )
        ]
        indexes = [models.Index(fields=("source_config", "data_category"))]

    def __str__(self) -> str:
        return f"{self.source_config.source_type}:{self.data_category}"
