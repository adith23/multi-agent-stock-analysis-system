from __future__ import annotations

from typing import Any

from engines.exceptions import EngineInputError
from ml.base import MLModel


class FinBERTClassifier(MLModel):
    """Lazy ProsusAI/finbert sentiment wrapper with injectable pipeline."""

    MODEL_NAME = "ProsusAI/finbert"

    def __init__(self, *, pipeline: Any | None = None, batch_size: int = 16) -> None:
        self._pipeline = pipeline
        self.batch_size = batch_size

    @property
    def pipeline(self):
        if self._pipeline is None:
            from transformers import pipeline

            self._pipeline = pipeline(
                "text-classification",
                model=self.MODEL_NAME,
                tokenizer=self.MODEL_NAME,
                top_k=None,
            )
        return self._pipeline

    def predict(self, inputs: Any) -> list[dict[str, Any]]:
        return self.classify(inputs)

    def classify(self, texts: list[str]) -> list[dict[str, Any]]:
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise EngineInputError("FinBERT inputs must be non-empty strings")
        raw = self.pipeline(
            texts,
            truncation=True,
            max_length=512,
            batch_size=self.batch_size,
        )
        results = []
        for text, scores in zip(texts, raw, strict=True):
            if isinstance(scores, dict):
                scores = [scores]
            mapped = {
                str(item["label"]).casefold().replace("label_", ""): float(item["score"])
                for item in scores
            }
            if set(mapped) == {"0", "1", "2"}:
                mapped = {
                    "positive": mapped["0"],
                    "negative": mapped["1"],
                    "neutral": mapped["2"],
                }
            sentiment = max(mapped, key=mapped.get)
            results.append(
                {
                    "text_preview": text[:100],
                    "sentiment": sentiment,
                    "confidence": round(mapped[sentiment], 8),
                    "scores": {key: round(value, 8) for key, value in mapped.items()},
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                }
            )
        return results
