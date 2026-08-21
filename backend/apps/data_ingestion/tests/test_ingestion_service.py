from datetime import UTC, datetime
from typing import Any

import pytest

from apps.data_ingestion.domain import DataCategory, IngestionStatus, SourceType
from apps.data_ingestion.models import (
    DataSourceConfiguration,
    NormalizedDataRecord,
    RawInputObject,
)
from apps.data_ingestion.services import IngestionService
from apps.market_data.models import NewsItem, OHLCVBar, Ticker


class FakeConnector:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def fetch_with_resilience(self, category: str, **params: Any):
        return self.records


@pytest.fixture
def finnhub_config(db):
    return DataSourceConfiguration.objects.create(
        source_type=SourceType.FINNHUB,
        display_name="Finnhub test",
        is_enabled=True,
        supported_categories=[DataCategory.OHLCV, DataCategory.NEWS],
    )


@pytest.mark.django_db
def test_ingestion_persists_provenance_and_projects_ohlcv(finnhub_config) -> None:
    payload = {
        "symbol": "aapl",
        "timestamp": "2026-07-29T00:00:00Z",
        "interval": "1d",
        "open": 100,
        "high": 110,
        "low": 95,
        "close": 105,
        "volume": 1000,
    }
    service = IngestionService()

    result = service.ingest(
        finnhub_config,
        DataCategory.OHLCV,
        connector=FakeConnector([payload]),
        symbol="AAPL",
    )

    assert result.accepted == 1
    normalized = NormalizedDataRecord.objects.get()
    assert normalized.status == IngestionStatus.ACCEPTED
    assert normalized.lineage["raw_input_id"] == str(normalized.raw_input_id)
    assert len(normalized.content_hash) == 64
    assert Ticker.objects.get().symbol == "AAPL"
    bar = OHLCVBar.objects.get()
    assert float(bar.close) == 105.0
    assert bar.source_type == SourceType.FINNHUB

    duplicate = service.ingest(
        finnhub_config,
        DataCategory.OHLCV,
        connector=FakeConnector([payload]),
        symbol="AAPL",
    )
    assert duplicate.duplicates == 1
    assert RawInputObject.objects.count() == 1

    # A source may add irrelevant raw metadata while the canonical observation
    # stays identical. This is still a normalized duplicate, not a failure.
    metadata_duplicate = service.ingest(
        finnhub_config,
        DataCategory.OHLCV,
        connector=FakeConnector([{**payload, "vendor_trace": "different"}]),
        symbol="AAPL",
    )
    assert metadata_duplicate.duplicates == 1
    assert RawInputObject.objects.count() == 2
    assert NormalizedDataRecord.objects.count() == 1


@pytest.mark.django_db
def test_near_duplicate_news_is_retained_but_not_projected_twice(
    finnhub_config,
) -> None:
    service = IngestionService()
    base = {
        "headline": "Acme announces quarterly earnings",
        "summary": "Revenue and profit increased",
        "datetime": datetime(2026, 7, 29, 10, tzinfo=UTC).timestamp(),
    }
    first = service.ingest(
        finnhub_config,
        DataCategory.NEWS,
        connector=FakeConnector([{**base, "url": "https://one.test"}]),
        symbol="ACME",
    )
    second = service.ingest(
        finnhub_config,
        DataCategory.NEWS,
        connector=FakeConnector([{**base, "url": "https://two.test"}]),
        symbol="ACME",
    )

    assert first.accepted == 1
    assert second.duplicates == 1
    assert NormalizedDataRecord.objects.count() == 2
    assert NewsItem.objects.count() == 1


@pytest.mark.django_db
def test_source_failure_is_isolated_and_observable(finnhub_config) -> None:
    class FailedConnector:
        def fetch_with_resilience(self, category: str, **params: Any):
            raise TimeoutError("provider unavailable")

    result = IngestionService().ingest(
        finnhub_config,
        DataCategory.OHLCV,
        connector=FailedConnector(),
        symbol="AAPL",
    )

    finnhub_config.refresh_from_db()
    assert result.failed == 1
    assert result.errors == ["TimeoutError: provider unavailable"]
    assert finnhub_config.last_failure_at is not None
    assert "provider unavailable" in finnhub_config.last_error


@pytest.mark.django_db
def test_raw_payload_is_immutable(finnhub_config) -> None:
    raw = RawInputObject.objects.create(
        source_config=finnhub_config,
        source_type=SourceType.FINNHUB,
        data_category=DataCategory.NEWS,
        raw_payload={"headline": "Original"},
        fetched_at=datetime.now(UTC),
        content_hash="a" * 64,
    )
    raw.raw_payload = {"headline": "Changed"}

    with pytest.raises(ValueError, match="immutable"):
        raw.save()
