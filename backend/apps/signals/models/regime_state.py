from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class RegimeState(TimeStampedModel, VersionedMixin):
    regime = models.CharField(max_length=60, db_index=True)
    probability = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    as_of = models.DateTimeField(db_index=True)
    indicators = models.JSONField(default=dict)
    alternatives = models.JSONField(default=dict)
    model_metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=("-as_of", "regime"))]
