from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .base_optimizer import OptimizationStrategy


class HierarchicalRiskParityOptimizer(OptimizationStrategy):
    """Hierarchical risk parity through the plan-mandated PyPortfolioOpt adapter."""

    def optimize(
        self,
        expected_returns: Any,
        covariance_matrix: Any,
        constraints: dict[str, Any],
    ) -> dict[str, float]:
        expected, covariance, assets, maximum_weight = self.inputs(
            expected_returns, covariance_matrix, constraints
        )
        from pypfopt import HRPOpt

        covariance_frame = pd.DataFrame(covariance, index=assets, columns=assets)
        raw = HRPOpt(cov_matrix=covariance_frame).optimize()
        weights = self.cap_and_normalize(
            np.asarray([raw[asset] for asset in assets]),
            maximum_weight,
        )
        return {
            asset: round(float(weight), 10) for asset, weight in zip(assets, weights, strict=True)
        }
