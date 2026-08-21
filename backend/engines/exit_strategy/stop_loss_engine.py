from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class StopLossEngine(DeterministicEngine):
    """Percentage, ATR, volatility, and Chandelier protective stops."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "entry_price")
        entry = float(inputs["entry_price"])
        if entry <= 0:
            raise EngineInputError("entry_price must be positive")
        percentage = float(inputs.get("stop_loss_pct", 0.08))
        atr = float(inputs.get("atr", 0))
        atr_multiple = float(inputs.get("atr_multiple", 2.0))
        volatility = float(inputs.get("annualized_volatility", 0))
        holding_days = int(inputs.get("holding_days", 20))
        highest = float(inputs.get("highest_price", entry))
        levels = {
            "percentage": entry * (1 - percentage),
            "atr": entry - atr_multiple * atr if atr else None,
            "volatility": entry
            * (
                1
                - float(inputs.get("volatility_multiplier", 1.0))
                * volatility
                * (holding_days / 252) ** 0.5
            ),
            "chandelier": (
                highest - float(inputs.get("chandelier_multiple", 3.0)) * atr if atr else None
            ),
        }
        valid = [value for value in levels.values() if value is not None and 0 < value < entry]
        selected = max(valid) if valid else entry * (1 - percentage)
        return {
            "stop_levels": {
                key: None if value is None else round(max(0.0, value), 8)
                for key, value in levels.items()
            },
            "recommended_stop": round(selected, 8),
            "risk_per_share": round(entry - selected, 8),
            "stop_loss_pct": round((entry - selected) / entry, 8),
            "engine_version": self.engine_version,
        }
