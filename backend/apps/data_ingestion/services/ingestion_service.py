from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from django.conf import settings
from django.db import IntegrityError, close_old_connections, transaction
from django.utils import timezone as django_timezone

from apps.core.utils.hashing import content_hash, redact_mapping
from apps.data_ingestion.connectors import ConnectorRegistry, connector_registry
from apps.data_ingestion.domain import (
    DataCategory,
    IngestionBatchResult,
    IngestionStatus,
    NormalizedRecordData,
    SourceType,
)
from apps.data_ingestion.models import (
    DataSourceConfiguration,
    NormalizedDataRecord,
    RawInputObject,
)
from apps.market_data.services import MarketDataProjector, MarketDataService

from .deduplication_service import DeduplicationService
from .normalization_service import NormalizationService
from .quality_service import DataQualityService

logger = logging.getLogger(__name__)


import math

def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return str(value)


class IngestionService:
    """Application service for resilient fetch-normalize-assess-persist flow."""

    SECRET_SETTING_NAMES = {
        SourceType.FINNHUB: "FINNHUB_API_KEY",
        SourceType.FRED: "FRED_API_KEY",
        SourceType.NEWS_API: "NEWS_API_KEY",
        SourceType.ALPHA_VANTAGE: "ALPHA_VANTAGE_API_KEY",
        SourceType.SEC_EDGAR: "SEC_EDGAR_IDENTITY",
    }

    def __init__(
        self,
        *,
        registry: ConnectorRegistry = connector_registry,
        normalization: NormalizationService | None = None,
        deduplication: DeduplicationService | None = None,
        quality: DataQualityService | None = None,
        projector: MarketDataProjector | None = None,
    ) -> None:
        self.registry = registry
        self.normalization = normalization or NormalizationService()
        self.deduplication = deduplication or DeduplicationService()
        self.quality = quality or DataQualityService()
        self.projector = projector or MarketDataProjector()

    def ingest(
        self,
        source_config: DataSourceConfiguration,
        category: str,
        *,
        connector=None,
        **params: Any,
    ) -> IngestionBatchResult:
        source = source_config.source_type
        result = IngestionBatchResult(source=source, category=category)
        if not source_config.is_enabled:
            result.errors.append("source_disabled")
            return result
        if not source_config.supports(category):
            result.errors.append("unsupported_category")
            return result

        source_connector = connector or self.registry.create(
            source,
            self._connector_config(source_config),
        )
        try:
            raw_records = source_connector.fetch_with_resilience(category, **params)
        except Exception as exc:
            self._mark_source_failure(source_config, exc)
            result.failed += 1
            result.errors.append(f"{type(exc).__name__}: {exc}")
            logger.exception(
                "data_source_fetch_failed",
                extra={"source": source, "category": category},
            )
            return result

        result.requested = len(raw_records)
        close_old_connections()
        for payload in raw_records:
            try:
                outcome, ids = self._process_payload(
                    source_config,
                    category,
                    _json_safe(payload),
                    params,
                )
                setattr(result, outcome, getattr(result, outcome) + 1)
                result.record_ids.extend(ids)
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"{type(exc).__name__}: {exc}")
                logger.exception(
                    "data_record_processing_failed",
                    extra={"source": source, "category": category},
                )
        self._mark_source_success(source_config)
        return result

    def _process_payload(
        self,
        source_config: DataSourceConfiguration,
        category: str,
        payload: dict[str, Any],
        request_params: Mapping[str, Any],
    ) -> tuple[str, list[str]]:
        source = source_config.source_type
        fingerprint = content_hash(payload)
        entity = str(request_params.get("symbol") or request_params.get("series_id") or "").upper()
        with transaction.atomic():
            try:
                raw = RawInputObject.objects.create(
                    source_config=source_config,
                    source_type=source,
                    data_category=category,
                    external_id=str(payload.get("id") or payload.get("uuid") or ""),
                    entity_identifier=entity,
                    raw_payload=payload,
                    fetched_at=django_timezone.now(),
                    request_metadata=redact_mapping(dict(_json_safe(request_params))),
                    content_hash=fingerprint,
                    status=IngestionStatus.PROCESSING,
                )
            except IntegrityError:
                return "duplicates", []

            normalized_values = self.normalization.normalize(
                payload,
                source_type=source,
                category=category,
                entity_identifier=entity,
            )
            ids: list[str] = []
            accepted_count = 0
            duplicate_count = 0
            rejected_count = 0
            for normalized in normalized_values:
                status, record = self._persist_normalized(raw, normalized)
                if status == IngestionStatus.ACCEPTED:
                    accepted_count += 1
                    self.projector.project(record)
                elif status == IngestionStatus.DUPLICATE:
                    duplicate_count += 1
                else:
                    rejected_count += 1
                ids.append(str(record.id))

            if accepted_count:
                raw.status = IngestionStatus.ACCEPTED
                outcome = "accepted"
            elif duplicate_count:
                raw.status = IngestionStatus.DUPLICATE
                outcome = "duplicates"
            else:
                raw.status = IngestionStatus.REJECTED
                outcome = "rejected"
            raw.save(update_fields=("status", "updated_at"))
            return outcome, ids

    def _persist_normalized(
        self,
        raw: RawInputObject,
        value: NormalizedRecordData,
    ) -> tuple[str, NormalizedDataRecord]:
        payload = _json_safe(value.payload)
        fingerprint = self.deduplication.exact_fingerprint(payload)
        existing = NormalizedDataRecord.objects.filter(
            source_type=str(value.source_type),
            data_category=str(value.category),
            content_hash=fingerprint,
        ).first()
        if existing is not None:
            return str(IngestionStatus.DUPLICATE), existing
        text = self.deduplication.searchable_text(str(value.category), payload)
        similarity_hash = self.deduplication.similarity_fingerprint(text) if text.strip() else ""
        near_duplicate = self.deduplication.find_near_duplicate(
            category=str(value.category), text=text
        )
        assessment = self.quality.assess(value)
        status = IngestionStatus.ACCEPTED
        if near_duplicate is not None:
            status = IngestionStatus.DUPLICATE
        elif not assessment.is_acceptable:
            status = IngestionStatus.REJECTED

        ticker = None
        if value.entity_identifier and value.category != DataCategory.MACRO:
            ticker = MarketDataService.resolve_ticker(value.entity_identifier)
        record = NormalizedDataRecord.objects.create(
            raw_input=raw,
            ticker=ticker,
            source_type=str(value.source_type),
            source_id=value.source_id,
            source_timestamp=value.source_timestamp,
            data_quality_score=assessment.score,
            content_hash=fingerprint,
            data_category=str(value.category),
            entity_identifier=value.entity_identifier,
            canonical_key=value.canonical_key,
            normalized_payload=payload,
            schema_version=value.schema_version,
            language=value.language,
            similarity_hash=similarity_hash,
            lineage={
                "raw_input_id": str(raw.id),
                "source_config_id": str(raw.source_config_id),
                "adapter_schema_version": value.schema_version,
                "near_duplicate_of": str(near_duplicate.id) if near_duplicate else None,
            },
            quality_issues=list(assessment.issues),
            quality_flags=assessment.flags,
            status=status,
        )
        return str(status), record

    @classmethod
    def _connector_config(cls, config: DataSourceConfiguration) -> dict[str, Any]:
        values = {
            **config.settings,
            "timeout_seconds": config.timeout_seconds,
            "retry_attempts": config.retry_attempts,
        }
        setting_name = cls.SECRET_SETTING_NAMES.get(SourceType(config.source_type))
        if setting_name:
            key = "identity" if config.source_type == SourceType.SEC_EDGAR else "api_key"
            values[key] = getattr(settings, setting_name, "")
        return values

    @staticmethod
    def _mark_source_success(config: DataSourceConfiguration) -> None:
        config.last_success_at = django_timezone.now()
        config.last_error = ""
        config.save(update_fields=("last_success_at", "last_error", "updated_at"))

    @staticmethod
    def _mark_source_failure(
        config: DataSourceConfiguration,
        error: Exception,
    ) -> None:
        config.last_failure_at = django_timezone.now()
        config.last_error = f"{type(error).__name__}: {error}"[:2000]
        config.save(update_fields=("last_failure_at", "last_error", "updated_at"))
