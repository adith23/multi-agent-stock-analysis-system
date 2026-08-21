from django.db import models

from apps.core.models import TimeStampedModel


class RegimeTransitionAlert(TimeStampedModel):
    previous_state = models.ForeignKey(
        "signals.RegimeState",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="outgoing_alerts",
    )
    current_state = models.ForeignKey(
        "signals.RegimeState", on_delete=models.CASCADE, related_name="incoming_alerts"
    )
    severity = models.CharField(
        max_length=20,
        choices=(("info", "Info"), ("warning", "Warning"), ("critical", "Critical")),
    )
    detected_at = models.DateTimeField(db_index=True)
    rationale = models.TextField(blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
