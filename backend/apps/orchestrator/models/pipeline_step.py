from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class StepStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class PipelineStepResult(TimeStampedModel, VersionedMixin):
    analysis_run = models.ForeignKey(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_name = models.CharField(max_length=80)
    sequence = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=20, choices=StepStatus.choices, default=StepStatus.PENDING
    )
    task_id = models.CharField(max_length=255, blank=True)
    attempt = models.PositiveSmallIntegerField(default=1)
    input_snapshot = models.JSONField(default=dict)
    output_snapshot = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    error_message = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("analysis_run", "step_name", "attempt"),
                name="uq_pipeline_step_run_name_attempt",
            )
        ]
        indexes = [models.Index(fields=("analysis_run", "sequence", "status"))]
        ordering = ("sequence", "attempt")
