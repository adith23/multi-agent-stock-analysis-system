from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from engines.exceptions import EngineInputError, InsufficientDataError
from ml.base import MLModel


class NewsAttentionDetector(MLModel):
    """EMA and rolling Z-score detector for news bursts and crowding."""

    MODEL_NAME = "news-attention-ema-zscore"

    def predict(self, inputs: Any) -> dict[str, Any]:
        counts = np.asarray(inputs["article_counts"], dtype=float)
        if counts.ndim != 1 or len(counts) < 10:
            raise InsufficientDataError("attention detection requires at least 10 periods")
        if not np.isfinite(counts).all() or (counts < 0).any():
            raise EngineInputError("article counts must be finite and non-negative")
        span = int(inputs.get("ema_span", 7))
        window = min(int(inputs.get("zscore_window", 20)), len(counts))
        series = pd.Series(counts)
        ema = series.ewm(span=span, adjust=False).mean()
        history = ema.iloc[-window:]
        std = float(history.iloc[:-1].std(ddof=0)) if len(history) > 1 else 0
        mean = float(history.iloc[:-1].mean()) if len(history) > 1 else float(history.iloc[-1])
        # A perfectly flat baseline has zero variance; retain sensitivity by
        # applying a small scale floor instead of suppressing the first burst.
        scale = max(std, abs(mean) * 0.1, 1e-9)
        zscore = (float(ema.iloc[-1]) - mean) / scale
        threshold = float(inputs.get("burst_zscore_threshold", 2.0))
        recent_baseline = float(series.iloc[-min(7, len(series)) : -1].mean())
        intensity = float(series.iloc[-1]) / max(recent_baseline, 1)
        return {
            "article_count": int(counts[-1]),
            "ema": round(float(ema.iloc[-1]), 6),
            "z_score": round(zscore, 6),
            "intensity_ratio": round(intensity, 6),
            "attention_level": (
                "extreme" if zscore >= 3 else ("elevated" if zscore >= threshold else "normal")
            ),
            "burst_detected": zscore >= threshold,
            "crowding_risk": zscore >= 3 or intensity >= 4,
            "model_name": self.model_name,
            "model_version": self.model_version,
        }
