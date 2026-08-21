from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_price_data(ticker: str, interval: str = "1d", limit: int = 252) -> list[dict[str, Any]]:
    """Fetch normalized OHLCV records in chronological order."""

    from apps.market_data.repositories import MarketDataRepository

    return MarketDataRepository().price_bars(ticker, interval=interval, limit=limit)
