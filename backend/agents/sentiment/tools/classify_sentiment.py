from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ml.finbert.classifier import FinBERTClassifier


@tool
def classify_sentiment(texts: list[str]) -> list[dict[str, Any]]:
    """Classify financial text with the lazily loaded FinBERT model."""

    return FinBERTClassifier().classify(texts)
