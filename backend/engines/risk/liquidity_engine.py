from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class LiquidityEngine(DeterministicEngine):
    """Participation-based days-to-liquidate and square-root market impact."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(
            inputs, "position_value", "average_daily_value", "bid_ask_spread_pct", "volatility"
        )
        position = float(inputs["position_value"])
        adv = float(inputs["average_daily_value"])
        spread = float(inputs["bid_ask_spread_pct"])
        volatility = float(inputs["volatility"])
        participation = float(inputs.get("maximum_participation_rate", 0.10))
        if min(position, adv, spread, volatility) < 0 or adv <= 0 or not 0 < participation <= 1:
            raise EngineInputError(
                "liquidity inputs must be non-negative with positive ADV/participation"
            )
        days = position / (adv * participation)
        participation_of_day = position / adv
        impact = spread / 2 + float(inputs.get("impact_coefficient", 0.5)) * volatility * (
            participation_of_day**0.5
        )
        maximum_days = float(inputs.get("maximum_days_to_liquidate", 5))
        score = max(0.0, min(100.0, 100 * (1 - days / max(maximum_days * 2, 1))))
        return {
            "days_to_liquidate": round(days, 4),
            "estimated_market_impact_pct": round(impact, 8),
            "estimated_cost": round(position * impact, 2),
            "liquidity_score": round(score, 2),
            "limit_breached": days > maximum_days,
            "engine_version": self.engine_version,
        }
