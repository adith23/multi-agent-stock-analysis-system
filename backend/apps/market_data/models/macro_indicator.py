from django.db import models

from apps.core.models import ProvenanceMixin, TimeStampedModel


class MacroIndicator(TimeStampedModel, ProvenanceMixin):
    series_id = models.CharField(max_length=50, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    observed_at = models.DateField(db_index=True)
    value = models.DecimalField(max_digits=28, decimal_places=10, null=True)
    frequency = models.CharField(max_length=30, blank=True)
    unit = models.CharField(max_length=80, blank=True)
    is_preliminary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("series_id", "observed_at", "source_type"),
                name="uq_macro_series_date_source",
            )
        ]
        indexes = [models.Index(fields=("series_id", "-observed_at"))]
