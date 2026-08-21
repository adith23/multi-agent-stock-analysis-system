from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any

from django.utils import timezone

from apps.orchestrator.models import AnalysisRun, PipelineStepResult, StepStatus


class PipelineStepService:
    def skip(
        self,
        run: AnalysisRun,
        *,
        name: str,
        sequence: int,
        reason: str,
    ) -> dict[str, Any]:
        now = timezone.now()
        PipelineStepResult.objects.update_or_create(
            analysis_run=run,
            step_name=name,
            attempt=1,
            defaults={
                "sequence": sequence,
                "status": StepStatus.SKIPPED,
                "warnings": [reason],
                "output_snapshot": {"skipped": True, "reason": reason},
                "started_at": now,
                "completed_at": now,
                "duration_ms": 0,
            },
        )
        return {"skipped": True, "reason": reason}

    @contextmanager
    def track(
        self,
        run: AnalysisRun,
        *,
        name: str,
        sequence: int,
        attempt: int = 1,
        input_snapshot: dict[str, Any] | None = None,
        task_id: str = "",
    ):
        step, _ = PipelineStepResult.objects.update_or_create(
            analysis_run=run,
            step_name=name,
            attempt=attempt,
            defaults={
                "sequence": sequence,
                "status": StepStatus.RUNNING,
                "input_snapshot": input_snapshot or {},
                "task_id": task_id,
                "started_at": timezone.now(),
                "error_message": "",
            },
        )
        started = time.monotonic()
        output: dict[str, Any] = {}
        try:
            yield output
        except Exception as exc:
            step.status = StepStatus.FAILED
            step.error_message = str(exc)[:4000]
            raise
        else:
            step.status = StepStatus.COMPLETED
            step.output_snapshot = output
        finally:
            step.completed_at = timezone.now()
            step.duration_ms = max(0, round((time.monotonic() - started) * 1000))
            step.save(
                update_fields=(
                    "status",
                    "output_snapshot",
                    "error_message",
                    "completed_at",
                    "duration_ms",
                    "updated_at",
                )
            )
