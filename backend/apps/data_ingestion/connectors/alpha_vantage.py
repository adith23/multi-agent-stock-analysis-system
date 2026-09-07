from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    ConnectorTransientError,
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
        request_params = {
            "function": functions[category],
            "symbol": symbol,
            "apikey": api_key,
        }
        if category == DataCategory.OHLCV:
            request_params["outputsize"] = "full"
        response = self.client.get(
            self.endpoint,
            params=request_params,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("Note") or payload.get("Information"):
            raise ConnectorTransientError(str(payload.get("Note") or payload.get("Information")))
        if payload.get("Error Message"):
            raise ValueError(str(payload["Error Message"]))
        if category == DataCategory.COMPANY_PROFILE:
            return self.as_records(payload)
        if category == DataCategory.QUOTE:
            quote = payload.get("Global Quote", {})
            if not quote:
                return []
            return [
                {
                    "symbol": quote.get("01. symbol") or symbol,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "current_price": quote.get("05. price"),
                    "open": quote.get("02. open"),
                    "high": quote.get("03. high"),
                    "low": quote.get("04. low"),
                    "previous_close": quote.get("08. previous close"),
                }
            ]
        series = payload.get("Time Series (Daily)", {})
        return [
            {
                "symbol": symbol,
                "timestamp": f"{observed_on}T00:00:00+00:00",
                "interval": "1d",
                "open": values.get("1. open"),
                "high": values.get("2. high"),
                "low": values.get("3. low"),
                "close": values.get("4. close"),
                "volume": values.get("5. volume", 0),
            }
            for observed_on, values in series.items()
        ]
