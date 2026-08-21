from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def fetch_macro_data(series_ids: list[str], limit: int = 24) -> list[dict[str, Any]]:
    """Fetch recent normalized macro observations from the canonical repository."""

    from apps.market_data.repositories import MarketDataRepository

    rows = MarketDataRepository().macro_observations(series_ids, per_series_limit=limit)
    return [
        {key: str(value) if value is not None else None for key, value in row.items()}
        for row in rows
    ]
