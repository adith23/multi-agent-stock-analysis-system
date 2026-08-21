from django.db import models

from apps.core.models import AuditMixin, TimeStampedModel, VersionedMixin


class RiskLimit(TimeStampedModel, VersionedMixin, AuditMixin):
    metric = models.CharField(max_length=80, unique=True)
    maximum = models.FloatField()
    severity = models.CharField(
        max_length=20,
        choices=(
            ("warning", "Warning"),
            ("reduce", "Reduce size"),
            ("escalate", "Escalate"),
            ("block", "Block"),
        ),
        default="block",
    )
    scope = models.CharField(max_length=30, default="portfolio")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
