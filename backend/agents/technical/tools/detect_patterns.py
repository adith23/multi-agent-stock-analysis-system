from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.technical.pattern_engine import PatternEngine


@tool
def detect_patterns(ohlcv: list[dict[str, Any]], atr: float = 0.0) -> dict[str, Any]:
    """Detect deterministic price, volume, gap, and reversal structures."""

    inputs: dict[str, Any] = {"ohlcv": ohlcv}
    if atr > 0:
        inputs["atr"] = atr
    return PatternEngine().compute(inputs)
