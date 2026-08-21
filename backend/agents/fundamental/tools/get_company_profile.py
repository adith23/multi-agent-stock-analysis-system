from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_company_profile(ticker: str) -> dict[str, Any]:
    """Fetch canonical company context for a ticker."""

    from apps.market_data.repositories import MarketDataRepository

    return MarketDataRepository().company_profile(ticker)
