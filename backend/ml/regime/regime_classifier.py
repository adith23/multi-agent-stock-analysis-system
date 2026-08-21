from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from engines.exceptions import EngineInputError, InsufficientDataError
from ml.base import MLModel


class RegimeClassifier(MLModel):
    """Gaussian HMM macro-regime classifier with persisted scaler/model."""

    MODEL_NAME = "gaussian-hmm-regime"

    def __init__(
        self,
        n_regimes: int = 5,
        *,
        model: Any | None = None,
        scaler: Any | None = None,
        model_path: str | None = None,
        regime_map: dict[int, str] | None = None,
    ) -> None:
        if n_regimes < 2:
            raise ValueError("n_regimes must be at least 2")
        self.n_regimes = n_regimes
        self.model = model
        self.scaler = scaler
        self.regime_map = {int(state): str(label) for state, label in (regime_map or {}).items()}
        if model_path and Path(model_path).exists():
            self.load(model_path)

    def _initialize(self) -> None:
        if self.model is None or self.scaler is None:
            from hmmlearn.hmm import GaussianHMM
            from sklearn.preprocessing import StandardScaler

            self.scaler = StandardScaler()
            self.model = GaussianHMM(
                n_components=self.n_regimes,
                covariance_type="full",
                n_iter=200,
                random_state=42,
            )

    @staticmethod
    def _features(inputs: Any) -> np.ndarray:
        features = np.asarray(inputs, dtype=float)
        if features.ndim != 2 or len(features) < 2 or not np.isfinite(features).all():
            raise EngineInputError("regime features must be a finite 2D array")
        return features

    def fit(self, features: Any) -> RegimeClassifier:
        values = self._features(features)
        if len(values) < self.n_regimes * 5:
            raise InsufficientDataError("HMM training requires at least 5 observations per regime")
        self._initialize()
        self.model.fit(self.scaler.fit_transform(values))
        return self

    def predict(self, inputs: Any) -> dict[str, Any]:
        values = self._features(inputs)
        self._initialize()
        if not hasattr(self.scaler, "mean_"):
            raise EngineInputError("regime classifier must be fitted or loaded before prediction")
        scaled = self.scaler.transform(values)
        states = self.model.predict(scaled)
        probabilities = self.model.predict_proba(scaled)
        current = int(states[-1])
        return {
            "regime": self.regime_map.get(current, f"regime_{current}"),
            "regime_id": current,
            "probability": round(float(probabilities[-1][current]), 8),
            "all_probabilities": {
                self.regime_map.get(index, f"regime_{index}"): round(
                    float(probabilities[-1][index]), 8
                )
                for index in range(self.n_regimes)
            },
            "transition_matrix": np.asarray(self.model.transmat_).tolist(),
            "model_name": self.model_name,
            "model_version": self.model_version,
        }

    def detect_transition(self, features: Any, *, lookback: int = 5) -> dict[str, Any]:
        values = self._features(features)
        if len(values) < lookback * 2:
            return {"transition_detected": False, "reason": "insufficient_history"}
        scaled = self.scaler.transform(values)
        states = self.model.predict(scaled)
        previous = int(np.bincount(states[-lookback * 2 : -lookback]).argmax())
        current = int(np.bincount(states[-lookback:]).argmax())
        return {
            "transition_detected": previous != current,
            "from_regime": self.regime_map.get(previous, f"regime_{previous}"),
            "to_regime": self.regime_map.get(current, f"regime_{current}"),
            "confidence": round(float((states[-lookback:] == current).mean()), 8),
        }

    def save(self, path: str) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "n_regimes": self.n_regimes,
                "regime_map": self.regime_map,
                "version": self.model_version,
            },
            destination,
        )

    def load(self, path: str) -> None:
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.n_regimes = int(data["n_regimes"])
        self.regime_map = {
            int(state): str(label) for state, label in data.get("regime_map", {}).items()
        }
