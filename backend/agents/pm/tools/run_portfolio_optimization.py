from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from engines.portfolio_optimization.hrp_optimizer import HierarchicalRiskParityOptimizer
from engines.portfolio_optimization.mean_variance_optimizer import MeanVarianceOptimizer
from engines.portfolio_optimization.risk_parity_optimizer import RiskParityOptimizer


@tool
def run_portfolio_optimization(
    methodology: str,
    expected_returns: list[float],
    covariance_matrix: list[list[float]],
    constraints: dict[str, Any],
) -> dict[str, float]:
    """Optimize target allocations using a configured Strategy."""

    strategies = {
        "mean_variance": MeanVarianceOptimizer,
        "hrp": HierarchicalRiskParityOptimizer,
        "risk_parity": RiskParityOptimizer,
    }
    strategy = strategies.get(methodology)
    if strategy is None:
        raise ValueError(f"unknown optimization methodology: {methodology}")
    return strategy().optimize(expected_returns, covariance_matrix, constraints)
