from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from apps.core.utils.hashing import content_hash
from apps.data_ingestion.domain import DataCategory
from apps.data_ingestion.models import DataPreparationRun, DataPreparationStatus
from apps.orchestrator.models import AnalysisRun
from apps.orchestrator.services.manifest_service import RunManifestService

from .data_readiness_service import AnalysisDataReadinessService, DataReadinessError
from .ingestion_lock import IngestionLock
from .ingestion_service import IngestionService
from .source_routing_service import SourceRoutingService


class AnalysisIngestionService:
    """Execute a persisted preparation plan with cache reuse and provider fallback."""

    aggregate_categories = frozenset({DataCategory.NEWS})

    def __init__(
        self,
        *,
        readiness: AnalysisDataReadinessService | None = None,
        router: SourceRoutingService | None = None,
        ingestion: IngestionService | None = None,
    ) -> None:
        self.readiness = readiness or AnalysisDataReadinessService()
        self.router = router or SourceRoutingService()
        self.ingestion = ingestion or IngestionService()

    def start(self, run_id: str) -> DataPreparationRun:
        run = AnalysisRun.objects.select_related("ticker").get(pk=run_id)
        try:
            preparation = run.data_preparation
        except DataPreparationRun.DoesNotExist:
            preparation = self.readiness.create_plan(run)
        now = timezone.now()
        preparation.status = DataPreparationStatus.RUNNING
        preparation.started_at = now
        preparation.save(update_fields=("status", "started_at", "updated_at"))
        return preparation

    def ingest_category(self, run_id: str, category: str) -> dict[str, Any]:
        run = AnalysisRun.objects.select_related("ticker", "data_preparation").get(pk=run_id)
        preparation = run.data_preparation
        entry = preparation.plan.get(category)
        if entry is None:
            return {"category": category, "status": "not_planned"}
        if not entry.get("fetch"):
            status = "historical_cache_only" if run.is_historical else "cache_hit"
            result = {"category": category, "status": status}
            self._set_category_result(preparation.id, category, result)
            return result

        candidates = self.router.candidates(category, ticker=run.ticker)
        if not candidates:
            inspection = self.readiness.inspect_category(
                run,
                category,
                knowledge_limit=timezone.now(),
            )
            blocking = bool(entry.get("required") and not inspection["gate_ready"])
            result = {
                "category": category,
                "status": "failed" if blocking else "degraded",
                "errors": ["no healthy, configured source is available"],
            }
            field = "errors" if blocking else "warnings"
            self._append(preparation.id, field, f"{category}: {result['errors'][0]}")
            self._set_category_result(preparation.id, category, result)
            return result

        attempts: list[dict[str, Any]] = []
        errors: list[str] = []
        successful_sources: list[str] = []
        for source_index, config in enumerate(candidates):
            source_succeeded = True
            source_produced_data = False
            for parameters in entry.get("parameter_sets", [{}]):
                lock_key = content_hash(
                    {
                        "ticker_id": str(run.ticker_id),
                        "category": category,
                        "provider": config.source_type,
                        "parameters": self._lock_parameters(category, parameters),
                    }
                )
                try:
                    with IngestionLock(lock_key).acquire():
                        if self._can_reuse_concurrent_result(
                            run,
                            category,
                            source=config.source_type,
                            parameters=parameters,
                        ):
                            attempts.append(
                                {
                                    "source": config.source_type,
                                    "parameters": parameters,
                                    "status": "reused_concurrent_result",
                                }
                            )
                            source_produced_data = True
                            continue
                        if not self.router.reserve_rate_limit(config):
                            raise RuntimeError("provider rate limit is exhausted")
                        batch = self.ingestion.ingest(
                            config,
                            category,
                            ticker=None if category == DataCategory.MACRO else run.ticker,
                            **self._connector_parameters(config.source_type, parameters),
                        )
                except Exception as exc:
                    source_succeeded = False
                    message = f"{config.source_type}: {type(exc).__name__}: {exc}"
                    errors.append(message)
                    attempts.append(
                        {
                            "source": config.source_type,
                            "parameters": parameters,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
                    break
                attempt = {
                    "source": config.source_type,
                    "parameters": parameters,
                    "status": "completed" if not batch.errors else "failed",
                    "requested": batch.requested,
                    "accepted": batch.accepted,
                    "duplicates": batch.duplicates,
                    "rejected": batch.rejected,
                    "failed": batch.failed,
                    "errors": batch.errors,
                }
                attempts.append(attempt)
                if batch.errors or batch.failed or not (batch.accepted or batch.duplicates):
                    source_succeeded = False
                    errors.extend(f"{config.source_type}: {error}" for error in batch.errors)
                    if not batch.errors:
                        errors.append(f"{config.source_type}: provider returned no usable records")
                    break
                source_produced_data = True
            if source_succeeded and source_produced_data:
                inspection = self.readiness.inspect_category(
                    run,
                    category,
                    knowledge_limit=timezone.now(),
                )
                if inspection["fresh"] or category in self.aggregate_categories:
                    successful_sources.append(config.source_type)
                    if category not in self.aggregate_categories:
                        break
                else:
                    source_succeeded = False
                    errors.append(
                        f"{config.source_type}: data remained incomplete or stale after ingestion"
                    )
            if not source_succeeded and source_index < len(candidates) - 1:
                self._append(
                    preparation.id,
                    "fallbacks",
                    {
                        "category": category,
                        "from": config.source_type,
                        "to": candidates[source_index + 1].source_type,
                    },
                )

        for attempt in attempts:
            self._append(preparation.id, "source_attempts", attempt)
        final_inspection = self.readiness.inspect_category(
            run,
            category,
            knowledge_limit=timezone.now(),
        )
        blocking = bool(entry.get("required") and not final_inspection["gate_ready"])
        result = {
            "category": category,
            "status": "completed" if successful_sources else "failed" if blocking else "degraded",
            "sources": successful_sources,
            "attempts": attempts,
            "errors": errors,
        }
        if errors and not successful_sources and blocking:
            self._append(preparation.id, "errors", *[f"{category}: {item}" for item in errors])
        elif errors:
            self._append(preparation.id, "warnings", *[f"{category}: {item}" for item in errors])
        self._set_category_result(preparation.id, category, result)
        return result

    def finalize(self, run_id: str) -> dict[str, Any]:
        run = AnalysisRun.objects.select_related("ticker", "data_preparation").get(pk=run_id)
        knowledge_cutoff = run.data_cutoff_at if run.is_historical else timezone.now()
        evaluation = self.readiness.evaluate(run, knowledge_cutoff=knowledge_cutoff)
        preparation = run.data_preparation
        preparation.status = evaluation["status"]
        preparation.selected_sources = evaluation["selected_sources"]
        preparation.warnings = list(
            dict.fromkeys([*preparation.warnings, *evaluation["warnings"]])
        )
        preparation.errors = list(dict.fromkeys([*preparation.errors, *evaluation["errors"]]))
        preparation.completed_at = timezone.now()
        preparation.save(
            update_fields=(
                "status",
                "selected_sources",
                "warnings",
                "errors",
                "completed_at",
                "updated_at",
            )
        )
        if evaluation["status"] == DataPreparationStatus.FAILED:
            raise DataReadinessError("; ".join(evaluation["errors"]))

        run.knowledge_cutoff_at = knowledge_cutoff
        run.run_manifest, run.configuration_hash, run.manifest_hash = RunManifestService.build(
            run_id=run.id,
            ticker=run.ticker,
            data_cutoff_at=run.data_cutoff_at,
            knowledge_cutoff_at=knowledge_cutoff,
            config=run.analysis_config,
            data_preparation={
                "id": str(preparation.id),
                "status": preparation.status,
                "cache_hits": preparation.cache_hits,
                "selected_sources": preparation.selected_sources,
                "category_results": preparation.category_results,
                "warnings": preparation.warnings,
            },
        )
        run.save(
            update_fields=(
                "knowledge_cutoff_at",
                "run_manifest",
                "configuration_hash",
                "manifest_hash",
                "updated_at",
            )
        )
        evaluation["knowledge_cutoff_at"] = knowledge_cutoff.isoformat()
        return evaluation

    def _can_reuse_concurrent_result(
        self,
        run: AnalysisRun,
        category: str,
        *,
        source: str,
        parameters: dict[str, Any],
    ) -> bool:
        if category == DataCategory.MACRO:
            return self.readiness.macro_series_is_fresh(
                run,
                series_id=str(parameters.get("series_id", "")),
                source=source,
                knowledge_limit=timezone.now(),
            )
        inspection = self.readiness.inspect_category(
            run,
            category,
            knowledge_limit=timezone.now(),
        )
        return bool(inspection["fresh"] and source in inspection["sources"])

    @staticmethod
    def _connector_parameters(source_type: str, parameters: dict[str, Any]) -> dict[str, Any]:
        values = dict(parameters)
        if source_type == "finnhub":
            for key in ("start", "end"):
                value = values.get(key)
                if not isinstance(value, str):
                    continue
                parsed = parse_datetime(value)
                if parsed is None:
                    parsed_date = parse_date(value)
                    parsed = (
                        datetime.combine(parsed_date, datetime.min.time())
                        if parsed_date is not None
                        else None
                    )
                if parsed is not None:
                    values[key] = parsed
        return values

    @staticmethod
    def _lock_parameters(category: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Canonicalize request windows so near-simultaneous runs share a lock."""
        values = {
            key: value
            for key, value in parameters.items()
            if key not in {"symbol", "exchange"}
        }
        if category in {
            DataCategory.COMPANY_PROFILE,
            DataCategory.FINANCIAL_STATEMENT,
            DataCategory.PEER_GROUP,
        }:
            values.pop("start", None)
            values.pop("end", None)
        for key in ("start", "end"):
            value = values.get(key)
            if isinstance(value, str):
                values[key] = value[:13] if category == DataCategory.NEWS else value[:10]
        return values

    @staticmethod
    @transaction.atomic
    def _append(preparation_id, field: str, *values: Any) -> None:
        if not values:
            return
        preparation = DataPreparationRun.objects.select_for_update().get(pk=preparation_id)
        current = list(getattr(preparation, field))
        current.extend(values)
        setattr(preparation, field, current)
        preparation.save(update_fields=(field, "updated_at"))

    @staticmethod
    @transaction.atomic
    def _set_category_result(preparation_id, category: str, result: dict[str, Any]) -> None:
        preparation = DataPreparationRun.objects.select_for_update().get(pk=preparation_id)
        values = dict(preparation.category_results)
        values[category] = result
        preparation.category_results = values
        preparation.save(update_fields=("category_results", "updated_at"))
