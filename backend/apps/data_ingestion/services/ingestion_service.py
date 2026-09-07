from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone as django_timezone

from apps.core.utils.hashing import content_hash, redact_mapping
from apps.data_ingestion.connectors import ConnectorRegistry, connector_registry
from apps.data_ingestion.domain import (
    DataCategory,
    IngestionBatchResult,
    IngestionStatus,
    NormalizationError,
    NormalizedRecordData,
    SourceType,
)
from apps.data_ingestion.models import (
    DataSourceCategoryHealth,
    DataSourceConfiguration,
    NormalizedDataRecord,
    RawInputObject,
)
from apps.market_data.services import MarketDataProjector, MarketDataService

from .deduplication_service import DeduplicationService
from .normalization_service import NormalizationService
from .quality_service import DataQualityService

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apps.market_data.models import Ticker


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

    DEFAULT_BATCH_SIZE = 500

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
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self.registry = registry
        self.normalization = normalization or NormalizationService()
        self.deduplication = deduplication or DeduplicationService()
        self.quality = quality or DataQualityService()
        self.projector = projector or MarketDataProjector()
        self.batch_size = max(1, batch_size)

    def ingest(
        self,
        source_config: DataSourceConfiguration,
        category: str,
        *,
        connector=None,
        ticker: Ticker | None = None,
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
            self._mark_source_failure(source_config, category, exc)
            result.failed += 1
            result.errors.append(f"{type(exc).__name__}: {exc}")
            logger.exception(
                "data_source_fetch_failed",
                extra={"source": source, "category": category},
            )
            return result

        result.requested = len(raw_records)
        close_old_connections()
        uses_bulk_path = category in MarketDataProjector.BULK_CATEGORIES and callable(
            getattr(self.projector, "project_many", None)
        )
        if uses_bulk_path:
            for offset in range(0, len(raw_records), self.batch_size):
                payloads = [_json_safe(payload) for payload in raw_records[offset : offset + self.batch_size]]
                try:
                    outcomes = self._process_payload_batch(
                        source_config,
                        category,
                        payloads,
                        params,
                        ticker=ticker,
                    )
                except Exception:
                    # Preserve record-level failure isolation if a database backend
                    # cannot perform the bulk upsert or a projector rejects a row.
                    logger.exception(
                        "data_batch_processing_failed_falling_back",
                        extra={"source": source, "category": category, "size": len(payloads)},
                    )
                    outcomes = []
                    for payload in payloads:
                        try:
                            outcomes.append(
                                self._process_payload(
                                    source_config,
                                    category,
                                    payload,
                                    params,
                                    ticker=ticker,
                                )
                            )
                        except Exception as exc:
                            outcomes.append(exc)
                self._accumulate_outcomes(result, outcomes, source=source, category=category)
        else:
            outcomes: list[tuple[str, list[str]] | Exception] = []
            for payload in raw_records:
                try:
                    outcomes.append(
                        self._process_payload(
                            source_config,
                            category,
                            _json_safe(payload),
                            params,
                            ticker=ticker,
                        )
                    )
                except Exception as exc:
                    outcomes.append(exc)
            self._accumulate_outcomes(result, outcomes, source=source, category=category)
        if result.failed:
            self._mark_source_failure(
                source_config,
                category,
                RuntimeError(f"{result.failed} record(s) failed during {category} ingestion"),
            )
        else:
            self._mark_source_success(source_config, category)
        return result

    @staticmethod
    def _accumulate_outcomes(
        result: IngestionBatchResult,
        outcomes: list[tuple[str, list[str]] | Exception],
        *,
        source: str,
        category: str,
    ) -> None:
        for item in outcomes:
            if isinstance(item, Exception):
                result.failed += 1
                result.errors.append(f"{type(item).__name__}: {item}")
                logger.error(
                    "data_record_processing_failed",
                    extra={"source": source, "category": category},
                    exc_info=(type(item), item, item.__traceback__),
                )
                continue
            outcome, ids = item
            setattr(result, outcome, getattr(result, outcome) + 1)
            result.record_ids.extend(ids)

    def _process_payload_batch(
        self,
        source_config: DataSourceConfiguration,
        category: str,
        payloads: list[dict[str, Any]],
        request_params: Mapping[str, Any],
        *,
        ticker: Ticker | None = None,
    ) -> list[tuple[str, list[str]] | Exception]:
        """Normalize and persist one bounded observation batch with set-based writes."""
        source = source_config.source_type
        entity = str(
            ticker.symbol
            if ticker is not None
            else request_params.get("symbol") or request_params.get("series_id") or ""
        ).upper()
        fingerprints = [content_hash(payload) for payload in payloads]
        existing_raw_hashes = set(
            RawInputObject.objects.filter(
                source_type=source,
                data_category=category,
                content_hash__in=fingerprints,
            ).values_list("content_hash", flat=True)
        )
        outcomes: list[tuple[str, list[str]] | Exception | None] = [None] * len(payloads)
        prepared: list[tuple[int, str, dict[str, Any], list[NormalizedRecordData]]] = []
        seen_raw_hashes = set(existing_raw_hashes)
        for index, (payload, fingerprint) in enumerate(zip(payloads, fingerprints, strict=True)):
            if fingerprint in seen_raw_hashes:
                outcomes[index] = ("duplicates", [])
                continue
            seen_raw_hashes.add(fingerprint)
            try:
                values = self.normalization.normalize(
                    payload,
                    source_type=source,
                    category=category,
                    entity_identifier=entity,
                )
                prepared.append((index, fingerprint, payload, values))
            except Exception as exc:
                outcomes[index] = exc

        if not prepared:
            return [item for item in outcomes if item is not None]

        now = django_timezone.now()
        metadata = redact_mapping(dict(_json_safe(request_params)))
        raw_candidates = {
            fingerprint: RawInputObject(
                source_config=source_config,
                source_type=source,
                data_category=category,
                content_hash=fingerprint,
                external_id=str(payload.get("id") or payload.get("uuid") or ""),
                entity_identifier=entity,
                raw_payload=payload,
                fetched_at=now,
                request_metadata=metadata,
                status=IngestionStatus.PROCESSING,
            )
            for _, fingerprint, payload, _ in prepared
        }

        with transaction.atomic():
            RawInputObject.objects.bulk_create(
                list(raw_candidates.values()),
                batch_size=self.batch_size,
                ignore_conflicts=True,
            )
            persisted_raw = {
                raw.content_hash: raw
                for raw in RawInputObject.objects.filter(
                    source_type=source,
                    data_category=category,
                    content_hash__in=raw_candidates,
                )
            }

            canonical_ticker = None if category == DataCategory.MACRO else ticker
            if canonical_ticker is None and entity and category != DataCategory.MACRO:
                canonical_ticker = MarketDataService.resolve_ticker(entity)

            normalized_entries: list[tuple[int, RawInputObject, NormalizedRecordData, str]] = []
            for index, raw_hash, _, values in prepared:
                raw = persisted_raw[raw_hash]
                # A concurrent worker won the raw-input insert. It owns normalization.
                if raw.id != raw_candidates[raw_hash].id:
                    outcomes[index] = ("duplicates", [])
                    continue
                for value in values:
                    payload = _json_safe(value.payload)
                    normalized_entries.append(
                        (index, raw, value, self.deduplication.exact_fingerprint(payload))
                    )

            normalized_hashes = [entry[3] for entry in normalized_entries]
            existing_records = {
                record.content_hash: record
                for record in NormalizedDataRecord.objects.filter(
                    source_type=source,
                    data_category=category,
                    content_hash__in=normalized_hashes,
                )
            }
            new_records: dict[str, NormalizedDataRecord] = {}
            statuses_by_index: dict[int, list[str]] = {}
            hashes_by_index: dict[int, list[str]] = {}
            for index, raw, value, fingerprint in normalized_entries:
                hashes_by_index.setdefault(index, []).append(fingerprint)
                if fingerprint in existing_records or fingerprint in new_records:
                    statuses_by_index.setdefault(index, []).append(str(IngestionStatus.DUPLICATE))
                    continue
                normalized_payload = _json_safe(value.payload)
                assessment = self.quality.assess(value)
                status = (
                    IngestionStatus.ACCEPTED
                    if assessment.is_acceptable
                    else IngestionStatus.REJECTED
                )
                record = NormalizedDataRecord(
                    raw_input=raw,
                    ticker=canonical_ticker,
                    source_type=str(value.source_type),
                    source_id=value.source_id,
                    source_timestamp=value.source_timestamp,
                    data_quality_score=assessment.score,
                    content_hash=fingerprint,
                    data_category=str(value.category),
                    entity_identifier=value.entity_identifier,
                    canonical_key=value.canonical_key,
                    normalized_payload=normalized_payload,
                    schema_version=value.schema_version,
                    language=value.language,
                    similarity_hash="",
                    lineage={
                        "raw_input_id": str(raw.id),
                        "source_config_id": str(raw.source_config_id),
                        "adapter_schema_version": value.schema_version,
                        "near_duplicate_of": None,
                    },
                    quality_issues=list(assessment.issues),
                    quality_flags=assessment.flags,
                    status=status,
                )
                new_records[fingerprint] = record
                statuses_by_index.setdefault(index, []).append(str(status))

            NormalizedDataRecord.objects.bulk_create(
                list(new_records.values()),
                batch_size=self.batch_size,
                ignore_conflicts=True,
            )
            persisted_records = {
                record.content_hash: record
                for record in NormalizedDataRecord.objects.select_related("ticker").filter(
                    source_type=source,
                    data_category=category,
                    content_hash__in=normalized_hashes,
                )
            }
            accepted_records = [
                persisted_records[fingerprint]
                for fingerprint, proposed in new_records.items()
                if persisted_records[fingerprint].id == proposed.id
                and proposed.status == IngestionStatus.ACCEPTED
            ]
            self.projector.project_many(accepted_records)

            raws_to_update: list[RawInputObject] = []
            for index, raw_hash, _, _ in prepared:
                if outcomes[index] is not None:
                    continue
                statuses = statuses_by_index.get(index, [])
                ids = [str(persisted_records[item].id) for item in hashes_by_index.get(index, [])]
                if str(IngestionStatus.ACCEPTED) in statuses:
                    outcome = "accepted"
                    raw_status = IngestionStatus.ACCEPTED
                elif str(IngestionStatus.DUPLICATE) in statuses:
                    outcome = "duplicates"
                    raw_status = IngestionStatus.DUPLICATE
                else:
                    outcome = "rejected"
                    raw_status = IngestionStatus.REJECTED
                raw = persisted_raw[raw_hash]
                raw.status = raw_status
                raw.updated_at = now
                raws_to_update.append(raw)
                outcomes[index] = (outcome, ids)
            RawInputObject.objects.bulk_update(
                raws_to_update,
                fields=("status", "updated_at"),
                batch_size=self.batch_size,
            )

        return [item for item in outcomes if item is not None]

    def _process_payload(
        self,
        source_config: DataSourceConfiguration,
        category: str,
        payload: dict[str, Any],
        request_params: Mapping[str, Any],
        *,
        ticker: Ticker | None = None,
    ) -> tuple[str, list[str]]:
        source = source_config.source_type
        fingerprint = content_hash(payload)
        entity = str(
            ticker.symbol
            if ticker is not None
            else request_params.get("symbol") or request_params.get("series_id") or ""
        ).upper()
        with transaction.atomic():
            raw, raw_created = RawInputObject.objects.get_or_create(
                source_type=source,
                data_category=category,
                content_hash=fingerprint,
                defaults={
                    "source_config": source_config,
                    "external_id": str(payload.get("id") or payload.get("uuid") or ""),
                    "entity_identifier": entity,
                    "raw_payload": payload,
                    "fetched_at": django_timezone.now(),
                    "request_metadata": redact_mapping(dict(_json_safe(request_params))),
                    "status": IngestionStatus.PROCESSING,
                },
            )

            # Existing financial payloads must be replayed so records accepted by
            # older adapters can be normalized and projected after an upgrade.
            if not raw_created and category != DataCategory.FINANCIAL_STATEMENT:
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
                status, record = self._persist_normalized(raw, normalized, ticker=ticker)
                if status == IngestionStatus.ACCEPTED:
                    self._project(record)
                    accepted_count += 1
                elif status == IngestionStatus.DUPLICATE:
                    if (
                        category == DataCategory.FINANCIAL_STATEMENT
                        and record.status == IngestionStatus.ACCEPTED
                    ):
                        self._project(record)
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
            if raw_created or accepted_count:
                raw.save(update_fields=("status", "updated_at"))
            return outcome, ids

    def _project(self, record: NormalizedDataRecord) -> object | None:
        projected = self.projector.project(record)
        if record.data_category == DataCategory.FINANCIAL_STATEMENT and projected is None:
            raise NormalizationError(
                "financial statement was normalized but not projected into the canonical store"
            )
        return projected

    def _persist_normalized(
        self,
        raw: RawInputObject,
        value: NormalizedRecordData,
        *,
        ticker: Ticker | None = None,
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

        canonical_ticker = None if value.category == DataCategory.MACRO else ticker
        if canonical_ticker is None and value.entity_identifier and value.category != DataCategory.MACRO:
            canonical_ticker = MarketDataService.resolve_ticker(value.entity_identifier)
        record = NormalizedDataRecord.objects.create(
            raw_input=raw,
            ticker=canonical_ticker,
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
    def _mark_source_success(config: DataSourceConfiguration, category: str) -> None:
        now = django_timezone.now()
        DataSourceCategoryHealth.objects.update_or_create(
            source_config=config,
            data_category=category,
            defaults={"last_success_at": now, "last_error": ""},
        )
        config.last_success_at = now
        config.last_error = ""
        config.save(update_fields=("last_success_at", "last_error", "updated_at"))

    @staticmethod
    def _mark_source_failure(
        config: DataSourceConfiguration,
        category: str,
        error: Exception,
    ) -> None:
        now = django_timezone.now()
        message = f"{type(error).__name__}: {error}"[:2000]
        DataSourceCategoryHealth.objects.update_or_create(
            source_config=config,
            data_category=category,
            defaults={
                "last_failure_at": now,
                "last_error": message,
            },
        )
        config.last_failure_at = now
        config.last_error = message
        config.save(update_fields=("last_failure_at", "last_error", "updated_at"))
