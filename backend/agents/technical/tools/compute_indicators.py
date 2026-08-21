from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.technical.indicator_engine import TechnicalIndicatorEngine


@tool
def compute_indicators(ohlcv: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the configured deterministic technical indicator set."""

    return TechnicalIndicatorEngine().compute({"ohlcv": ohlcv})
