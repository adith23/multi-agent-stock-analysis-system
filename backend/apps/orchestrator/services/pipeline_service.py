from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.market_data.models import Ticker

from ..models import AnalysisRun, AnalysisScope
from .manifest_service import RunManifestService


class PipelineService:
    @transaction.atomic
    def create_run(
        self,
        *,
        ticker: Ticker,
        initiated_by,
        config: dict[str, Any] | None = None,
        scope: str = AnalysisScope.SINGLE,
        data_cutoff_at=None,
        idempotency_key: str | None = None,
        request_hash: str = "",
        is_historical: bool = False,
    ) -> AnalysisRun:
        data_cutoff_at = data_cutoff_at or timezone.now()
        run = AnalysisRun(
            ticker=ticker,
            initiated_by=initiated_by,
            analysis_config=config or {},
            scope=scope,
            data_cutoff_at=data_cutoff_at,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            is_historical=is_historical,
        )
        run.checkpoint_thread_id = f"analysis-{run.id}"
        (
            run.run_manifest,
            run.configuration_hash,
            run.manifest_hash,
        ) = RunManifestService.build(
            run_id=run.id,
            ticker=ticker,
            data_cutoff_at=data_cutoff_at,
            config=run.analysis_config,
        )
        run.save()
        AuditService.record_event(
            action=AuditAction.CREATE,
            event_type="analysis.created",
            actor=initiated_by,
            resource_type="AnalysisRun",
            resource_id=str(run.id),
            summary=f"Analysis created for {ticker.symbol}",
            metadata={
                "manifest_hash": run.manifest_hash,
                "data_cutoff_at": data_cutoff_at.isoformat(),
            },
        )
        return run

    def dispatch(self, run: AnalysisRun) -> str:
        from config.task_backend import dispatch_task

        task_id = dispatch_task(
            "apps.orchestrator.tasks.run_full_pipeline",
            args=(str(run.id),),
            queue="orchestrator",
        )
        run.celery_task_id = task_id
        run.save(update_fields=("celery_task_id", "updated_at"))
        return task_id
