from __future__ import annotations

from typing import Any

from apps.data_ingestion.domain import DataCategory, SourceType

from .base import BaseConnector


class YFinanceConnector(BaseConnector):
    source_type = SourceType.YFINANCE
    supported_categories = frozenset(
        {
            DataCategory.QUOTE,
            DataCategory.OHLCV,
            DataCategory.COMPANY_PROFILE,
            DataCategory.FINANCIAL_STATEMENT,
            DataCategory.NEWS,
        }
    )

    def _ticker(self, symbol: str):
        if self._client is not None:
            return self._client
        import yfinance as yf

        return yf.Ticker(symbol)

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        symbol = str(params.get("symbol", "AAPL" if params.get("health_check") else "")).upper()
        if not symbol:
            raise ValueError("symbol is required")
        ticker = self._ticker(symbol)
        if params.get("health_check"):
            return [{"symbol": symbol}]
        if category in {DataCategory.QUOTE, DataCategory.COMPANY_PROFILE}:
            return self.as_records(getattr(ticker, "info", {}))
        if category == DataCategory.NEWS:
            return self.as_records(getattr(ticker, "news", []))
        if category == DataCategory.FINANCIAL_STATEMENT:
            statement = getattr(ticker, params.get("statement", "financials"))
            return [{"symbol": symbol, "statement": statement.to_dict()}]
        history = ticker.history(
            start=params.get("start"),
            end=params.get("end"),
            period=params.get("period", "1mo"),
            interval=params.get("interval", "1d"),
            auto_adjust=False,
        )
        records: list[dict[str, Any]] = []
        for timestamp, row in history.iterrows():
            item = {str(key).lower().replace(" ", "_"): value for key, value in row.items()}
            item.update({"timestamp": timestamp.isoformat(), "symbol": symbol})
            records.append(item)
        return records
