from __future__ import annotations

from abc import ABC
from typing import Any

import numpy as np

from apps.core.domain.interfaces import IOptimizationStrategy
from engines.exceptions import EngineInputError


class OptimizationStrategy(IOptimizationStrategy, ABC):
    """Shared constraint validation for replaceable allocation strategies."""

    @staticmethod
    def inputs(
        expected_returns: Any,
        covariance_matrix: Any,
        constraints: dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray, list[str], float]:
        expected = np.asarray(expected_returns, dtype=float)
        covariance = np.asarray(covariance_matrix, dtype=float)
        if expected.ndim != 1 or covariance.shape != (len(expected), len(expected)):
            raise EngineInputError("expected returns and covariance dimensions must match")
        if not np.isfinite(expected).all() or not np.isfinite(covariance).all():
            raise EngineInputError("optimization inputs must be finite")
        assets = list(constraints.get("assets", [str(i) for i in range(len(expected))]))
        if len(assets) != len(expected):
            raise EngineInputError("assets must match expected returns")
        maximum_weight = float(constraints.get("maximum_weight", 1.0))
        if not 0 < maximum_weight <= 1 or maximum_weight * len(expected) < 1:
            raise EngineInputError("maximum_weight makes full investment infeasible")
        return expected, covariance, assets, maximum_weight

    @staticmethod
    def cap_and_normalize(weights: np.ndarray, maximum_weight: float) -> np.ndarray:
        weights = np.maximum(weights, 0)
        for _ in range(100):
            weights = weights / weights.sum()
            overflow = np.maximum(weights - maximum_weight, 0).sum()
            weights = np.minimum(weights, maximum_weight)
            if overflow < 1e-12:
                break
            available = weights < maximum_weight - 1e-12
            if not available.any():
                break
            weights[available] += overflow / available.sum()
        return weights / weights.sum()
