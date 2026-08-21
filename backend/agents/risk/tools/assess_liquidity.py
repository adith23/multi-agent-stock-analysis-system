from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.risk.liquidity_engine import LiquidityEngine


@tool
def assess_liquidity(liquidity_inputs: dict[str, Any]) -> dict[str, Any]:
    """Compute days-to-liquidate and estimated execution impact."""

    return LiquidityEngine().compute(liquidity_inputs)
