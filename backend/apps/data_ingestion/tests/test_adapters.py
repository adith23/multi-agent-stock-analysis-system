from datetime import UTC, datetime

import pytest

from apps.data_ingestion.adapters import MacroAdapter, NewsAdapter, PriceAdapter
from apps.data_ingestion.domain import DataCategory, NormalizationError
from apps.data_ingestion.services import DataQualityService


def test_price_adapter_expands_finnhub_candle_arrays() -> None:
    records = PriceAdapter().normalize(
        {
            "t": [1_700_000_000, 1_700_086_400],
            "o": [10, 11],
            "h": [12, 13],
            "l": [9, 10],
            "c": [11, 12],
            "v": [1000, 1200],
        },
        source_type="finnhub",
        category=DataCategory.OHLCV,
        entity_identifier="aapl",
    )

    assert len(records) == 2
    assert records[0].entity_identifier == "AAPL"
    assert records[0].payload["interval"] == "1d"
    assert records[1].canonical_key.startswith("ohlcv:AAPL:1d:")


def test_news_adapter_normalizes_provider_shape() -> None:
    record = NewsAdapter().normalize(
        {
            "title": "Company reports results",
            "description": "Summary",
            "publishedAt": "2026-07-29T10:00:00Z",
            "source": {"name": "Wire"},
            "url": "https://example.test/story",
        },
        source_type="news_api",
        category=DataCategory.NEWS,
        entity_identifier="MSFT",
    )[0]

    assert record.payload["publisher"] == "Wire"
    assert record.payload["symbols"] == ["MSFT"]
    assert record.source_timestamp == datetime(2026, 7, 29, 10, tzinfo=UTC)


def test_macro_adapter_rejects_missing_observation_date() -> None:
    with pytest.raises(NormalizationError):
        MacroAdapter().normalize(
            {"series_id": "FEDFUNDS", "value": 4.5},
            source_type="fred",
            category=DataCategory.MACRO,
        )


def test_quality_service_rejects_invalid_ohlcv_range() -> None:
    record = PriceAdapter().normalize(
        {
            "symbol": "AAPL",
            "timestamp": "2026-07-29T00:00:00Z",
            "open": 10,
            "high": 8,
            "low": 9,
            "close": 10,
            "volume": 100,
        },
        source_type="finnhub",
        category=DataCategory.OHLCV,
    )[0]
    result = DataQualityService().assess(
        record,
        now=datetime(2026, 7, 29, 1, tzinfo=UTC),
    )

    assert result.is_acceptable is False
    assert result.flags["malformed"] is True
    assert "invalid_ohlcv_range" in result.issues
