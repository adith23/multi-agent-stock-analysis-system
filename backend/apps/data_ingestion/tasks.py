from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from apps.data_ingestion.domain import DataCategory
from apps.data_ingestion.models import DataSourceConfiguration
from apps.data_ingestion.services import IngestionService

logger = logging.getLogger(__name__)

FRED_SERIES = (
    "FEDFUNDS",
    "CPIAUCSL",
    "CPILFESL",
    "GDPC1",
    "UNRATE",
    "DGS10",
    "DGS2",
    "T10Y2Y",
    "VIXCLS",
    "MANEMP",
    "UMCSENT",
    "ICSA",
    "BAAFFM",
    "M2SL",
    "SP500",
)


@shared_task(
    bind=True,
    autoretry_for=(),
    name="apps.data_ingestion.tasks.ingest_source",
    soft_time_limit=540,
    time_limit=600,
)
def ingest_source(
    self,
    source_type: str,
    category: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = DataSourceConfiguration.objects.get(source_type=source_type)
    result = IngestionService().ingest(config, category, **(params or {}))
    return result.model_dump(mode="json")


@shared_task(name="apps.data_ingestion.tasks.ingest_enabled_sources")
def ingest_enabled_sources(categories: list[str] | None = None) -> dict[str, Any]:
    requested_categories = set(categories or DataCategory.values)
    scheduled: list[str] = []
    skipped: list[str] = []
    for config in DataSourceConfiguration.objects.filter(is_enabled=True).order_by("priority"):
        for category in config.supported_categories:
            if category not in requested_categories:
                continue
            parameter_sets = _parameter_sets(config, category)
            if not parameter_sets:
                skipped.append(f"{config.source_type}:{category}:no_entities_configured")
                continue
            for params in parameter_sets:
                task = ingest_source.delay(config.source_type, category, params)
                scheduled.append(task.id)
    return {"scheduled_task_ids": scheduled, "skipped": skipped}


def _parameter_sets(
    config: DataSourceConfiguration,
    category: str,
) -> list[dict[str, Any]]:
    if category == DataCategory.MACRO:
        return [
            {"series_id": series_id}
            for series_id in config.settings.get("series_ids", FRED_SERIES)
        ]
    symbols = config.settings.get("symbols", [])
    if category == DataCategory.NEWS and not symbols:
        queries = config.settings.get("queries", [])
        return [{"query": query} for query in queries]
    return [{"symbol": symbol} for symbol in symbols]
