from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_news(ticker: str, lookback_days: int = 30, limit: int = 100) -> list[dict[str, Any]]:
    """Fetch normalized, provenance-bearing news for a ticker."""

    from apps.market_data.repositories import MarketDataRepository

    return MarketDataRepository().news(ticker, lookback_days=lookback_days, limit=limit)
