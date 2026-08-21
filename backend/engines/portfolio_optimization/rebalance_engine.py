from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class RebalanceEngine(DeterministicEngine):
    """Generate value trades only where target drift exceeds tolerance."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "current_weights", "target_weights", "portfolio_value")
        current = inputs["current_weights"]
        target = inputs["target_weights"]
        if set(current) != set(target):
            raise EngineInputError("current and target portfolios must have identical assets")
        threshold = float(inputs.get("drift_threshold", 0.02))
        value = float(inputs["portfolio_value"])
        trades = []
        for asset in target:
            drift = float(target[asset]) - float(current[asset])
            if abs(drift) >= threshold:
                trades.append(
                    {
                        "asset": asset,
                        "action": "buy" if drift > 0 else "sell",
                        "weight_change": round(drift, 8),
                        "value": round(abs(drift) * value, 2),
                    }
                )
        return {
            "rebalance_required": bool(trades),
            "trades": trades,
            "turnover": round(
                sum(
                    trade["weight_change"] if trade["weight_change"] > 0 else 0 for trade in trades
                ),
                8,
            ),
            "engine_version": self.engine_version,
        }
