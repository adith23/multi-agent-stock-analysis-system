from django.db import models

from apps.core.models import AuditMixin, TimeStampedModel, VersionedMixin


class ComplianceRule(TimeStampedModel, VersionedMixin, AuditMixin):
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=255)
    field = models.CharField(max_length=120)
    operator = models.CharField(
        max_length=20,
        choices=(
            ("eq", "Equals"),
            ("ne", "Not equal"),
            ("lt", "Less than"),
            ("lte", "Less than or equal"),
            ("gt", "Greater than"),
            ("gte", "Greater than or equal"),
            ("in", "In"),
            ("not_in", "Not in"),
        ),
    )
    expected_value = models.JSONField()
    severity = models.CharField(
        max_length=20,
        choices=(("warning", "Warning"), ("approval", "Approval"), ("block", "Block")),
        default="block",
    )
    description = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(default=100)
    is_active = models.BooleanField(default=True, db_index=True)
