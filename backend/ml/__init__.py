"""Lazy, versioned machine-learning model wrappers."""

from .base import MLModel
from .registry import MLModelRegistry, ml_model_registry


def register_default_models() -> None:
    from .attention import NewsAttentionDetector
    from .finbert import FinBERTClassifier
    from .regime import RegimeClassifier

    ml_model_registry.register("finbert", FinBERTClassifier)
    ml_model_registry.register("attention", NewsAttentionDetector)
    ml_model_registry.register("regime", RegimeClassifier)


register_default_models()

__all__ = ["MLModel", "MLModelRegistry", "ml_model_registry", "register_default_models"]
