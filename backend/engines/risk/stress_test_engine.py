from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class StressTestEngine(DeterministicEngine):
    """Apply asset and factor shock scenarios to current positions."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "positions", "scenarios")
        positions = {str(key): float(value) for key, value in inputs["positions"].items()}
        if not positions or any(value < 0 for value in positions.values()):
            raise EngineInputError("positions must be non-empty and non-negative")
        total = sum(positions.values())
        factor_exposures = inputs.get("factor_exposures", {})
        results = []
        for scenario in inputs["scenarios"]:
            asset_shocks = scenario.get("asset_shocks", {})
            factor_shocks = scenario.get("factor_shocks", {})
            asset_impacts = {
                symbol: value * float(asset_shocks.get(symbol, scenario.get("market_shock", 0)))
                for symbol, value in positions.items()
            }
            factor_impact = 0.0
            factor_impacts: dict[str, float] = {}
            for factor, shock in factor_shocks.items():
                exposure = float(factor_exposures.get(factor, 0))
                impact = total * exposure * float(shock)
                factor_impacts[factor] = impact
                factor_impact += impact
            pnl = sum(asset_impacts.values()) + factor_impact
            results.append(
                {
                    "name": scenario.get("name", "unnamed"),
                    "stressed_pnl": round(pnl, 2),
                    "stressed_return": round(self.safe_divide(pnl, total), 8),
                    "asset_impacts": {k: round(v, 2) for k, v in asset_impacts.items()},
                    "factor_impacts": {k: round(v, 2) for k, v in factor_impacts.items()},
                    "breaches_loss_limit": (
                        self.safe_divide(-pnl, total)
                        > float(inputs.get("maximum_loss_pct", np.inf))
                    ),
                }
            )
        worst = min(results, key=lambda result: result["stressed_pnl"])
        return {
            "scenarios": results,
            "worst_scenario": worst["name"],
            "worst_loss": worst["stressed_pnl"],
            "engine_version": self.engine_version,
        }
