from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.domain.enums import PipelineStatus
from apps.core.models import TimeStampedModel
from apps.core.utils.hashing import content_hash


class AnalysisScope(models.TextChoices):
    SINGLE = "single", "Single security"
    WATCHLIST = "watchlist", "Watchlist"
    SECTOR = "sector", "Sector"
    UNIVERSE = "universe", "Universe"


class AnalysisRun(TimeStampedModel):
    """Auditable state machine for one controlled research workflow."""

    ticker = models.ForeignKey(
        "market_data.Ticker",
        on_delete=models.PROTECT,
        related_name="analysis_runs",
    )
    scope = models.CharField(
        max_length=20, choices=AnalysisScope.choices, default=AnalysisScope.SINGLE
    )
    status = models.CharField(
        max_length=40,
        choices=PipelineStatus.choices(),
        default=PipelineStatus.PENDING,
        db_index=True,
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analysis_runs",
    )
    analysis_config = models.JSONField(default=dict)
    data_cutoff_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    run_manifest = models.JSONField(default=dict, editable=False)
    configuration_hash = models.CharField(max_length=64, default="", editable=False)
    manifest_hash = models.CharField(
        max_length=64,
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    request_hash = models.CharField(max_length=64, blank=True, editable=False)
    celery_task_id = models.CharField(max_length=255, blank=True)
    checkpoint_thread_id = models.CharField(max_length=255, unique=True)
    current_stage = models.CharField(max_length=60, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    VALID_TRANSITIONS = {
        PipelineStatus.PENDING: {PipelineStatus.INGESTING, PipelineStatus.CANCELLED},
        PipelineStatus.INGESTING: {
            PipelineStatus.EXTRACTING_SIGNALS,
            PipelineStatus.FAILED,
        },
        PipelineStatus.EXTRACTING_SIGNALS: {
            PipelineStatus.RUNNING_SPECIALISTS,
            PipelineStatus.FAILED,
        },
        PipelineStatus.RUNNING_SPECIALISTS: {
            PipelineStatus.PEER_ANALYSIS,
            PipelineStatus.FAILED,
        },
        PipelineStatus.PEER_ANALYSIS: {
            PipelineStatus.ADVERSARIAL_REVIEW,
            PipelineStatus.FAILED,
        },
        PipelineStatus.ADVERSARIAL_REVIEW: {
            PipelineStatus.CONVICTION_SCORING,
            PipelineStatus.FAILED,
        },
        PipelineStatus.CONVICTION_SCORING: {
            PipelineStatus.RISK_VALIDATION,
            PipelineStatus.FAILED,
        },
        PipelineStatus.RISK_VALIDATION: {
            PipelineStatus.COMPLIANCE_CHECK,
            PipelineStatus.FAILED,
        },
        PipelineStatus.COMPLIANCE_CHECK: {
            PipelineStatus.POSITION_SIZING,
            PipelineStatus.BLOCKED,
            PipelineStatus.FAILED,
        },
        PipelineStatus.POSITION_SIZING: {
            PipelineStatus.PORTFOLIO_OPTIMIZATION,
            PipelineStatus.FAILED,
        },
        PipelineStatus.PORTFOLIO_OPTIMIZATION: {
            PipelineStatus.PM_SYNTHESIS,
            PipelineStatus.FAILED,
        },
        PipelineStatus.PM_SYNTHESIS: {
            PipelineStatus.AWAITING_PM_APPROVAL,
            PipelineStatus.FAILED,
        },
        PipelineStatus.AWAITING_PM_APPROVAL: {
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        },
    }

    class Meta:
        indexes = [
            models.Index(fields=("ticker", "-created_at")),
            models.Index(fields=("status", "-created_at")),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("initiated_by", "idempotency_key"),
                condition=models.Q(idempotency_key__isnull=False),
                name="uq_analysis_user_idempotency_key",
            )
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.configuration_hash:
            self.configuration_hash = content_hash(self.analysis_config)
        if not self.run_manifest:
            self.run_manifest = {
                "schema_version": "legacy-direct-create",
                "analysis_run_id": str(self.id),
                "data_cutoff_at": self.data_cutoff_at.isoformat(),
                "configuration_hash": self.configuration_hash,
            }
            self.manifest_hash = content_hash(self.run_manifest)
        elif not self.manifest_hash:
            self.manifest_hash = content_hash(self.run_manifest)
        super().save(*args, **kwargs)

    def transition_to(self, new_status: PipelineStatus | str, *, save: bool = True) -> None:
        target = PipelineStatus(new_status)
        current = PipelineStatus(self.status)
        if target == current:
            return
        if target not in self.VALID_TRANSITIONS.get(current, set()):
            raise ValueError(f"invalid pipeline transition: {current} -> {target}")
        self.status = target
        self.current_stage = target
        now = timezone.now()
        if target is PipelineStatus.INGESTING and self.started_at is None:
            self.started_at = now
        if target in {
            PipelineStatus.BLOCKED,
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        }:
            self.completed_at = now
        if save:
            self.save(
                update_fields=(
                    "status",
                    "current_stage",
                    "started_at",
                    "completed_at",
                    "updated_at",
                )
            )

    def fail(self, message: str) -> None:
        if self.status not in {
            PipelineStatus.COMPLETED,
            PipelineStatus.BLOCKED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        }:
            self.status = PipelineStatus.FAILED
            self.current_stage = PipelineStatus.FAILED
            self.error_message = message[:4000]
            self.completed_at = timezone.now()
            self.save(
                update_fields=(
                    "status",
                    "current_stage",
                    "error_message",
                    "completed_at",
                    "updated_at",
                )
            )
