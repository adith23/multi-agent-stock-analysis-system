"""Base Django models shared by domain entities."""

from __future__ import annotations

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Use non-sequential identifiers for domain entities."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(UUIDModel):
    """Add immutable creation and automatically maintained update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)
