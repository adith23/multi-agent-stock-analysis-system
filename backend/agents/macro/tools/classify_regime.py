from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ml.regime.regime_classifier import RegimeClassifier


@tool
def classify_regime(features: list[list[float]], model_path: str) -> dict[str, Any]:
    """Classify a macro feature matrix with the persisted Gaussian HMM."""

    return RegimeClassifier(model_path=model_path).predict(features)
