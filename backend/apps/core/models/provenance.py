"""Abstract provenance, actor, and versioning mixins."""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ProvenanceMixin(models.Model):
    """Track source identity, freshness, quality, and content lineage."""

    source_type = models.CharField(max_length=50, db_index=True)
    source_id = models.CharField(max_length=255, blank=True)
    source_timestamp = models.DateTimeField(null=True, blank=True)
    effective_at = models.DateTimeField(null=True, blank=True, db_index=True)
    available_at = models.DateTimeField(default=timezone.now, db_index=True)
    revision_id = models.CharField(max_length=100, blank=True)
    vintage_date = models.DateField(null=True, blank=True, db_index=True)
    ingestion_timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    data_quality_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    content_hash = models.CharField(max_length=64, db_index=True)

    class Meta:
        abstract = True


class AuditMixin(models.Model):
    """Record the authenticated actors responsible for model mutations."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True


class VersionedMixin(models.Model):
    """Retain schema, agent, model, and prompt versions for reproducibility."""

    version = models.PositiveIntegerField(default=1)
    agent_version = models.CharField(max_length=50, blank=True)
    model_version = models.CharField(max_length=50, blank=True)
    prompt_version = models.CharField(max_length=50, blank=True)

    class Meta:
        abstract = True
