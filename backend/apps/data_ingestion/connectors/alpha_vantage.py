from __future__ import annotations

from typing import Any

from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    DataCategory,
    SourceType,
)

from .base import BaseConnector


class AlphaVantageConnector(BaseConnector):
    source_type = SourceType.ALPHA_VANTAGE
    supported_categories = frozenset(
        {DataCategory.QUOTE, DataCategory.OHLCV, DataCategory.COMPANY_PROFILE}
    )
    endpoint = "https://www.alphavantage.co/query"

    @property
    def client(self):
        if self._client is None:
            import httpx

            self._client = httpx.Client(timeout=float(self.config.get("timeout_seconds", 30)))
        return self._client

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        api_key = self.config.get("api_key")
        if not api_key:
            raise ConnectorConfigurationError("ALPHA_VANTAGE_API_KEY is required")
        symbol = str(params.get("symbol", "AAPL" if params.get("health_check") else "")).upper()
        functions = {
            DataCategory.QUOTE: "GLOBAL_QUOTE",
            DataCategory.OHLCV: "TIME_SERIES_DAILY",
            DataCategory.COMPANY_PROFILE: "OVERVIEW",
        }
        response = self.client.get(
            self.endpoint,
            params={"function": functions[category], "symbol": symbol, "apikey": api_key},
        )
        response.raise_for_status()
        return self.as_records(response.json())
