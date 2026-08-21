from __future__ import annotations

from typing import Any

import pandas as pd

from .base_optimizer import OptimizationStrategy


class MeanVarianceOptimizer(OptimizationStrategy):
    """Long-only maximum-utility Markowitz allocation."""

    def optimize(
        self,
        expected_returns: Any,
        covariance_matrix: Any,
        constraints: dict[str, Any],
    ) -> dict[str, float]:
        expected, covariance, assets, maximum_weight = self.inputs(
            expected_returns, covariance_matrix, constraints
        )
        from pypfopt import EfficientFrontier

        expected_series = pd.Series(expected, index=assets)
        covariance_frame = pd.DataFrame(covariance, index=assets, columns=assets)
        optimizer = EfficientFrontier(expected_series, covariance_frame)
        optimizer.add_constraint(lambda weights: weights <= maximum_weight)
        optimizer.max_quadratic_utility(risk_aversion=float(constraints.get("risk_aversion", 3.0)))
        return {
            asset: round(float(weight), 10) for asset, weight in optimizer.clean_weights().items()
        }
