from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.technical.relative_strength_engine import RelativeStrengthEngine


@tool
def measure_relative_strength(
    asset_prices: list[float],
    benchmark_prices: list[float],
) -> dict[str, Any]:
    """Compare asset and benchmark performance on a risk-adjusted basis."""

    return RelativeStrengthEngine().compute(
        {"asset_prices": asset_prices, "benchmark_prices": benchmark_prices}
    )
