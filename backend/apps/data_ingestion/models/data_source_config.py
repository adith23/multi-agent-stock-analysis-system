from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.data_ingestion.domain.enums import SourceType


class DataSourceConfiguration(TimeStampedModel):
    """Non-secret source policy used by connector orchestration."""

    source_type = models.CharField(max_length=30, choices=SourceType.choices, unique=True)
    display_name = models.CharField(max_length=120)
    is_enabled = models.BooleanField(default=False, db_index=True)
    priority = models.PositiveSmallIntegerField(default=100)
    supported_categories = models.JSONField(default=list)
    settings = models.JSONField(default=dict, blank=True)
    requests_per_minute = models.PositiveIntegerField(default=60)
    timeout_seconds = models.PositiveIntegerField(default=30)
    retry_attempts = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1)])
    stale_after_seconds = models.PositiveIntegerField(default=3600)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ("priority", "source_type")

    def supports(self, category: str) -> bool:
        return category in self.supported_categories

    def __str__(self) -> str:
        return self.display_name
