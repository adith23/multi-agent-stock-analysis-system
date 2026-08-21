from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class ScenarioEngine(DeterministicEngine):
    """User-defined linear factor and idiosyncratic what-if simulation."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "positions", "factor_exposures", "factor_shocks")
        positions = {str(key): float(value) for key, value in inputs["positions"].items()}
        total = sum(positions.values())
        if total <= 0:
            raise EngineInputError("positions must have positive value")
        idiosyncratic = inputs.get("asset_shocks", {})
        impacts = {}
        for asset, value in positions.items():
            factor_impact = sum(
                float(inputs["factor_exposures"].get(asset, {}).get(factor, 0)) * float(shock)
                for factor, shock in inputs["factor_shocks"].items()
            )
            total_shock = factor_impact + float(idiosyncratic.get(asset, 0))
            impacts[asset] = {
                "shock": round(total_shock, 8),
                "pnl": round(value * total_shock, 2),
                "stressed_value": round(value * (1 + total_shock), 2),
            }
        pnl = sum(item["pnl"] for item in impacts.values())
        return {
            "name": inputs.get("name", "custom"),
            "asset_impacts": impacts,
            "portfolio_pnl": round(pnl, 2),
            "portfolio_return": round(pnl / total, 8),
            "stressed_value": round(total + pnl, 2),
            "engine_version": self.engine_version,
        }
