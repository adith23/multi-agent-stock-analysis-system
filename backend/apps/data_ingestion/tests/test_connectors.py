from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest

from apps.data_ingestion.connectors import (
    AlphaVantageConnector,
    BaseConnector,
    ConnectorRegistry,
    FinnhubConnector,
    FredConnector,
    NewsApiConnector,
    SecEdgarConnector,
    YFinanceConnector,
)
from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    ConnectorTransientError,
    DataCategory,
    SourceType,
)


class StubConnector(BaseConnector):
    source_type = SourceType.FINNHUB
    supported_categories = frozenset({DataCategory.QUOTE})

    def __init__(self, *args, failures: int = 0, **kwargs) -> None:
        self.failures = failures
        self.calls = 0
        super().__init__(*args, **kwargs)

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        self.calls += 1
        if self.calls <= self.failures:
            raise ConnectorTransientError("temporary")
        return [{"c": 100}]


def test_base_connector_retries_transient_failures() -> None:
    connector = StubConnector(
        {"retry_attempts": 3, "retry_initial_seconds": 0, "retry_max_seconds": 0},
        failures=2,
    )

    assert connector.fetch_with_resilience(DataCategory.QUOTE) == [{"c": 100}]
    assert connector.calls == 3


def test_registry_is_an_abstract_factory() -> None:
    registry = ConnectorRegistry()
    registry.register(SourceType.FINNHUB, StubConnector)

    connector = registry.create(SourceType.FINNHUB, {"retry_attempts": 1})

    assert isinstance(connector, StubConnector)
    assert registry.available_sources() == ("finnhub",)
    with pytest.raises(ConnectorConfigurationError):
        registry.create(SourceType.FRED)


def test_finnhub_connector_dispatches_supported_endpoints() -> None:
    client = Mock()
    client.quote.return_value = {"c": 100}
    client.company_profile2.return_value = {"name": "Acme"}
    client.company_peers.return_value = ["MSFT"]
    connector = FinnhubConnector({"retry_attempts": 1}, client=client)

    assert connector.fetch(DataCategory.QUOTE, symbol="AAPL") == [{"c": 100}]
    assert connector.fetch(DataCategory.COMPANY_PROFILE, symbol="AAPL") == [{"name": "Acme"}]
    assert connector.fetch(DataCategory.PEER_GROUP, symbol="AAPL") == [
        {"symbol": "AAPL", "peers": ["MSFT"]}
    ]
    client.quote.assert_called_once_with("AAPL")


def test_fred_connector_maps_series_and_metadata() -> None:
    client = Mock()
    client.get_series.return_value = {date(2026, 7, 1): 4.5}
    client.get_series_info.return_value = SimpleNamespace(
        title="Federal Funds Rate",
        frequency="Monthly",
        units="Percent",
    )

    records = FredConnector({"retry_attempts": 1}, client=client).fetch(
        DataCategory.MACRO,
        series_id="fedfunds",
    )

    assert records == [
        {
            "series_id": "FEDFUNDS",
            "date": "2026-07-01",
            "value": 4.5,
            "title": "Federal Funds Rate",
            "frequency": "Monthly",
            "units": "Percent",
        }
    ]


def test_news_api_connector_extracts_articles() -> None:
    client = Mock()
    client.get_everything.return_value = {"articles": [{"title": "Markets"}]}

    records = NewsApiConnector({"retry_attempts": 1}, client=client).fetch(
        DataCategory.NEWS,
        query="stocks",
    )

    assert records == [{"title": "Markets"}]
    assert client.get_everything.call_args.kwargs["q"] == "stocks"


def test_yfinance_connector_converts_history_rows() -> None:
    row = SimpleNamespace(
        items=lambda: [
            ("Open", 10),
            ("High", 12),
            ("Low", 9),
            ("Close", 11),
            ("Volume", 100),
        ]
    )
    timestamp = SimpleNamespace(isoformat=lambda: "2026-07-29T00:00:00+00:00")
    history = SimpleNamespace(iterrows=lambda: [(timestamp, row)])
    ticker = Mock()
    ticker.history.return_value = history

    records = YFinanceConnector({"retry_attempts": 1}, client=ticker).fetch(
        DataCategory.OHLCV,
        symbol="aapl",
    )

    assert records[0]["symbol"] == "AAPL"
    assert records[0]["close"] == 11


def test_sec_connector_converts_column_oriented_filing_data() -> None:
    filings = Mock()
    latest = Mock()
    latest.to_dict.return_value = {
        "form": {0: "10-K"},
        "accession_number": {0: "0001"},
    }
    filings.latest.return_value = latest
    company = Mock()
    company.get_filings.return_value = filings

    records = SecEdgarConnector({"retry_attempts": 1}, client=company).fetch(
        DataCategory.FILING,
        symbol="AAPL",
    )

    assert records == [{"form": "10-K", "accession_number": "0001"}]
    company.get_filings.assert_called_once_with(form=["10-K", "10-Q", "8-K"])


def test_alpha_vantage_connector_uses_http_client() -> None:
    response = Mock()
    response.json.return_value = {"Global Quote": {"05. price": "100"}}
    client = Mock()
    client.get.return_value = response
    connector = AlphaVantageConnector(
        {"api_key": "test", "retry_attempts": 1},
        client=client,
    )

    assert connector.fetch(DataCategory.QUOTE, symbol="AAPL") == [
        {"Global Quote": {"05. price": "100"}}
    ]
    response.raise_for_status.assert_called_once()
