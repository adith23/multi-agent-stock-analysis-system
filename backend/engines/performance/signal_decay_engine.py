from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class SignalDecayEngine(DeterministicEngine):
    """Estimate exponential alpha decay and half-life by log-linear fit."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "horizons", "mean_returns")
        horizons = self.vector(inputs["horizons"], name="horizons", minimum_length=3)
        returns = self.vector(inputs["mean_returns"], name="mean_returns", minimum_length=3)
        if len(horizons) != len(returns) or (horizons < 0).any():
            raise EngineInputError("horizons and returns must align with non-negative horizons")
        absolute = np.abs(returns)
        valid = absolute > 1e-12
        if valid.sum() < 2:
            return {
                "decay_rate": 0.0,
                "half_life": None,
                "recalibration_recommended": True,
                "engine_version": self.engine_version,
            }
        slope, intercept = np.polyfit(horizons[valid], np.log(absolute[valid]), 1)
        decay_rate = max(0.0, float(-slope))
        half_life = float(np.log(2) / decay_rate) if decay_rate > 0 else None
        fitted = np.exp(intercept + slope * horizons)
        residual = float(np.sqrt(np.mean((absolute - fitted) ** 2)))
        threshold = float(inputs.get("minimum_half_life", 5))
        return {
            "decay_rate": round(decay_rate, 8),
            "half_life": None if half_life is None else round(half_life, 4),
            "fit_rmse": round(residual, 8),
            "recalibration_recommended": half_life is None or half_life < threshold,
            "engine_version": self.engine_version,
        }
