from unittest.mock import Mock, patch

import pytest

from apps.data_ingestion.domain import DataCategory, SourceType
from apps.data_ingestion.models import DataSourceConfiguration
from apps.data_ingestion.tasks import FRED_SERIES, _parameter_sets, ingest_enabled_sources


@pytest.mark.django_db
def test_scheduler_isolates_configured_entities_per_task() -> None:
    DataSourceConfiguration.objects.create(
        source_type=SourceType.YFINANCE,
        display_name="Fallback",
        is_enabled=True,
        supported_categories=[DataCategory.OHLCV],
        settings={"symbols": ["AAPL", "MSFT"]},
    )
    async_result = Mock(id="task-id")
    with patch(
        "apps.data_ingestion.tasks.ingest_source.delay", return_value=async_result
    ) as delay:
        result = ingest_enabled_sources([DataCategory.OHLCV])

    assert result == {"scheduled_task_ids": ["task-id", "task-id"], "skipped": []}
    assert delay.call_count == 2


def test_fred_parameter_defaults_cover_required_series() -> None:
    config = Mock(settings={})

    values = _parameter_sets(config, DataCategory.MACRO)

    assert len(values) == 15
    assert {item["series_id"] for item in values} == set(FRED_SERIES)
