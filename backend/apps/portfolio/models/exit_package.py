from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class ExitPackageStatus(models.TextChoices):
    PENDING = "pending", "Pending approval"
    ACTIVE = "active", "Active"
    TRIGGERED = "triggered", "Triggered"
    CLOSED = "closed", "Closed"


class ExitStrategyPackage(TimeStampedModel, VersionedMixin):
    analysis_run = models.OneToOneField(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="exit_package",
    )
    status = models.CharField(
        max_length=20,
        choices=ExitPackageStatus.choices,
        default=ExitPackageStatus.PENDING,
        db_index=True,
    )
    entry_price = models.DecimalField(max_digits=24, decimal_places=8)
    stop_loss_price = models.DecimalField(max_digits=24, decimal_places=8)
    stop_loss_pct = models.FloatField()
    profit_targets = models.JSONField(default=list)
    trailing_stop = models.JSONField(default=dict)
    thesis_invalidation_triggers = models.JSONField(default=list)
    time_based_review_date = models.DateTimeField()
    current_price = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    trigger_type = models.CharField(max_length=60, blank=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        was_triggered = False
        if self.pk:
            previous = ExitStrategyPackage.objects.filter(pk=self.pk).values("status").first()
            if previous and previous["status"] != ExitPackageStatus.TRIGGERED and self.status == ExitPackageStatus.TRIGGERED:
                was_triggered = True
        elif self.status == ExitPackageStatus.TRIGGERED:
            was_triggered = True

        super().save(*args, **kwargs)

        if was_triggered:
            try:
                from django.utils import timezone
                from apps.core.events import EventBus

                price = float(self.current_price or self.stop_loss_price or 0.0)
                ticker_sym = ""
                if hasattr(self, "analysis_run") and hasattr(self.analysis_run, "ticker"):
                    ticker_sym = self.analysis_run.ticker.symbol

                EventBus.publish_alert_event(
                    "exit_trigger",
                    {
                        "ticker": ticker_sym,
                        "trigger": self.trigger_type or "stop_loss",
                        "price": price,
                        "detected_at": self.triggered_at.isoformat() if self.triggered_at else timezone.now().isoformat(),
                    },
                    event_id=str(self.id),
                )
            except Exception:
                pass
