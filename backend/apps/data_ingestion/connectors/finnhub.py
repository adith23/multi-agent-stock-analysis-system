from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    DataCategory,
    SourceType,
)

from .base import BaseConnector


class FinnhubConnector(BaseConnector):
    source_type = SourceType.FINNHUB
    supported_categories = frozenset(
        {
            DataCategory.QUOTE,
            DataCategory.OHLCV,
            DataCategory.COMPANY_PROFILE,
            DataCategory.FINANCIAL_STATEMENT,
            DataCategory.NEWS,
            DataCategory.PEER_GROUP,
            DataCategory.INSIDER_TRANSACTION,
            DataCategory.OWNERSHIP,
        }
    )

    @property
    def client(self):
        if self._client is None:
            api_key = self.config.get("api_key")
            if not api_key:
                raise ConnectorConfigurationError("FINNHUB_API_KEY is required")
            import finnhub

            self._client = finnhub.Client(api_key=api_key)
        return self._client

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        symbol = str(params.get("symbol", "")).upper()
        if params.get("health_check"):
            return self.as_records(self.client.quote(symbol or "AAPL"))
        if category != DataCategory.NEWS and not symbol:
            raise ValueError("symbol is required")

        now = datetime.now(UTC)
        start = params.get("start", now - timedelta(days=30))
        end = params.get("end", now)
        start_date = start.date() if isinstance(start, datetime) else start
        end_date = end.date() if isinstance(end, datetime) else end

        if category == DataCategory.QUOTE:
            payload = self.client.quote(symbol)
        elif category == DataCategory.OHLCV:
            payload = self.client.stock_candles(
                symbol,
                params.get("resolution", "D"),
                int(datetime.combine(start_date, datetime.min.time(), tzinfo=UTC).timestamp()),
                int(datetime.combine(end_date, datetime.max.time(), tzinfo=UTC).timestamp()),
            )
        elif category == DataCategory.COMPANY_PROFILE:
            payload = self.client.company_profile2(symbol=symbol)
        elif category == DataCategory.FINANCIAL_STATEMENT:
            payload = self.client.company_basic_financials(symbol, params.get("metric", "all"))
        elif category == DataCategory.NEWS:
            news_symbol = symbol or str(params.get("query", "")).upper()
            payload = self.client.company_news(
                news_symbol,
                _from=start_date.isoformat(),
                to=end_date.isoformat(),
            )
        elif category == DataCategory.PEER_GROUP:
            payload = {"symbol": symbol, "peers": self.client.company_peers(symbol)}
        elif category == DataCategory.INSIDER_TRANSACTION:
            payload = self.client.stock_insider_transactions(
                symbol,
                start_date.isoformat(),
                end_date.isoformat(),
            )
        elif category == DataCategory.OWNERSHIP:
            payload = self.client.ownership(symbol)
        else:
            payload = []
        return self.as_records(payload)
