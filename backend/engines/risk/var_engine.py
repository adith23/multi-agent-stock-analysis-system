from __future__ import annotations

from statistics import NormalDist
from typing import Any

import numpy as np

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class ValueAtRiskEngine(DeterministicEngine):
    """Parametric, historical, and seeded Monte Carlo VaR/CVaR."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "returns")
        returns = self.matrix(inputs["returns"], name="returns")
        if returns.shape[0] < 30:
            from engines.exceptions import InsufficientDataError

            raise InsufficientDataError("VaR requires at least 30 return observations")
        weights = self.normalized_weights(inputs.get("weights", np.ones(returns.shape[1])))
        if len(weights) != returns.shape[1]:
            raise EngineInputError("weights must match return columns")
        confidence_levels = tuple(
            float(level) for level in inputs.get("confidence_levels", (0.95, 0.99))
        )
        if any(not 0.5 < level < 1 for level in confidence_levels):
            raise EngineInputError("confidence levels must be between 0.5 and 1")
        horizon = int(inputs.get("horizon_days", 1))
        if horizon < 1:
            raise EngineInputError("horizon_days must be positive")
        portfolio_value = float(inputs.get("portfolio_value", 1.0))
        portfolio_returns = returns @ weights
        mean = float(portfolio_returns.mean())
        volatility = float(portfolio_returns.std(ddof=1))
        rng = np.random.default_rng(int(inputs.get("random_seed", 42)))
        simulations = rng.normal(
            mean * horizon,
            volatility * np.sqrt(horizon),
            size=int(inputs.get("simulations", 20_000)),
        )
        results: dict[str, Any] = {}
        for confidence in confidence_levels:
            alpha = 1 - confidence
            z = NormalDist().inv_cdf(alpha)
            parametric_loss = -(mean * horizon + z * volatility * np.sqrt(horizon))
            historical_horizon = portfolio_returns * np.sqrt(horizon)
            historical_cutoff = float(np.quantile(historical_horizon, alpha))
            monte_carlo_cutoff = float(np.quantile(simulations, alpha))
            tail = historical_horizon[historical_horizon <= historical_cutoff]
            results[f"{confidence:.2f}"] = {
                "parametric_var_pct": round(max(0.0, parametric_loss), 8),
                "historical_var_pct": round(max(0.0, -historical_cutoff), 8),
                "monte_carlo_var_pct": round(max(0.0, -monte_carlo_cutoff), 8),
                "historical_cvar_pct": round(max(0.0, -float(tail.mean())), 8),
                "parametric_var_amount": round(max(0.0, parametric_loss) * portfolio_value, 2),
            }
        return {
            "confidence_results": results,
            "horizon_days": horizon,
            "portfolio_volatility_daily": round(volatility, 8),
            "observations": len(portfolio_returns),
            "engine_version": self.engine_version,
        }
