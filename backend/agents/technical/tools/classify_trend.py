from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.technical.trend_classifier import TrendClassifier


@tool
def classify_trend(current_price: float, indicators: dict[str, Any]) -> dict[str, Any]:
    """Classify current trend and timing from deterministic indicators."""

    return TrendClassifier().compute(
        {
            "current_price": current_price,
            "sma_20": indicators["sma_20"],
            "sma_50": indicators["sma_50"],
            "rsi": indicators["rsi_14"],
            "macd_histogram": indicators["macd_histogram"],
        }
    )
