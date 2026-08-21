from django.db import models

from apps.core.models import TimeStampedModel


class Sector(TimeStampedModel):
    """Normalized sector/industry classification."""

    name = models.CharField(max_length=120)
    industry = models.CharField(max_length=160, blank=True)
    classification_system = models.CharField(max_length=30, default="GICS")
    code = models.CharField(max_length=30, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("name", "industry", "classification_system"),
                name="uq_sector_classification",
            )
        ]
        ordering = ("name", "industry")

    def __str__(self) -> str:
        return f"{self.name} / {self.industry}" if self.industry else self.name
