from __future__ import annotations

from typing import Any

import numpy as np

from .base_optimizer import OptimizationStrategy


class RiskParityOptimizer(OptimizationStrategy):
    """Iterative equal-risk-contribution allocator."""

    def optimize(
        self,
        expected_returns: Any,
        covariance_matrix: Any,
        constraints: dict[str, Any],
    ) -> dict[str, float]:
        expected, covariance, assets, maximum_weight = self.inputs(
            expected_returns, covariance_matrix, constraints
        )
        count = len(expected)
        weights = np.ones(count) / count
        target = np.asarray(constraints.get("risk_budgets", np.ones(count) / count), dtype=float)
        target = target / target.sum()
        for _ in range(int(constraints.get("maximum_iterations", 1000))):
            marginal = covariance @ weights
            total_risk = float(np.sqrt(max(weights @ marginal, 1e-16)))
            contributions = weights * marginal / total_risk
            desired = target * total_risk
            adjustment = np.divide(
                desired,
                contributions,
                out=np.ones_like(desired),
                where=np.abs(contributions) > 1e-16,
            )
            updated = self.cap_and_normalize(
                weights * np.sqrt(np.maximum(adjustment, 0)), maximum_weight
            )
            if np.max(np.abs(updated - weights)) < 1e-9:
                weights = updated
                break
            weights = updated
        return {
            asset: round(float(weight), 10) for asset, weight in zip(assets, weights, strict=True)
        }
