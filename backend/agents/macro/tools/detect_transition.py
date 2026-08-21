from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ml.regime.regime_classifier import RegimeClassifier


@tool
def detect_transition(
    features: list[list[float]],
    model_path: str,
    lookback: int = 5,
) -> dict[str, Any]:
    """Detect a persistent HMM regime transition over a configured lookback."""

    return RegimeClassifier(model_path=model_path).detect_transition(features, lookback=lookback)
