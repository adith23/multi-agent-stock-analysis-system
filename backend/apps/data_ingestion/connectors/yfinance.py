from __future__ import annotations

from datetime import date, datetime
from typing import Any

from apps.data_ingestion.domain import DataCategory, SourceType

from .base import BaseConnector


class YFinanceConnector(BaseConnector):
    FINANCIAL_STATEMENTS = {
        "income": "financials",
        "balance_sheet": "balance_sheet",
        "cash_flow": "cashflow",
    }
    STATEMENT_ALIASES = {
        "balance": "balance_sheet",
        "balance_sheet": "balance_sheet",
        "balancesheet": "balance_sheet",
        "cash_flow": "cash_flow",
        "cashflow": "cash_flow",
        "financials": "income",
        "income": "income",
        "income_statement": "income",
    }

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
            return self._financial_statements(
                ticker,
                symbol=symbol,
                requested=params.get("statement"),
                currency=params.get("currency", "USD"),
            )
        start = self._history_date(params.get("start"))
        end = self._history_date(params.get("end"))
        history_params = {
            "start": start,
            "end": end,
            "interval": params.get("interval", "1d"),
            "auto_adjust": False,
        }
        # Yahoo accepts at most two of period/start/end. Explicit windows are
        # authoritative, so do not forward period when both bounds are present.
        if start is None or end is None:
            history_params["period"] = params.get("period", "1mo")
        history = ticker.history(**history_params)
        records: list[dict[str, Any]] = []
        for timestamp, row in history.iterrows():
            item = {str(key).lower().replace(" ", "_"): value for key, value in row.items()}
            item.update({"timestamp": timestamp.isoformat(), "symbol": symbol})
            records.append(item)
        return records

    @staticmethod
    def _history_date(value: Any) -> Any:
        """Return Yahoo-compatible date strings for timestamp-shaped windows."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if not isinstance(value, str):
            return value
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return value

    def _financial_statements(
        self,
        ticker,
        *,
        symbol: str,
        requested: Any = None,
        currency: Any = "USD",
    ) -> list[dict[str, Any]]:
        if requested:
            normalized = str(requested).strip().lower().replace("-", "_").replace(" ", "_")
            statement_type = self.STATEMENT_ALIASES.get(normalized)
            if statement_type is None:
                supported = ", ".join(sorted(self.FINANCIAL_STATEMENTS))
                raise ValueError(
                    f"unsupported statement {requested!r}; expected one of: {supported}"
                )
            statement_types = (statement_type,)
        else:
            statement_types = tuple(self.FINANCIAL_STATEMENTS)

        records = []
        for statement_type in statement_types:
            frame = getattr(ticker, self.FINANCIAL_STATEMENTS[statement_type])
            if frame is None or getattr(frame, "empty", False):
                continue
            records.append(
                {
                    "symbol": symbol,
                    "statement_type": statement_type,
                    "currency": str(currency or "USD").upper(),
                    "statement": frame.to_dict(),
                }
            )
        if not records:
            raise ValueError(f"no financial statements returned for {symbol}")
        return records
