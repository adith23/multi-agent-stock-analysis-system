from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_financials(ticker: str, limit: int = 12) -> list[dict[str, Any]]:
    """Fetch versioned normalized statements for a ticker."""

    from apps.market_data.repositories import MarketDataRepository

    return MarketDataRepository().financial_statements(ticker, limit=limit)
