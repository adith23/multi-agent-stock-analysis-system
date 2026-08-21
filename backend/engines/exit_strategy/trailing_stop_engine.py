from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class TrailingStopEngine(DeterministicEngine):
    """State-free trailing stop calculator and trigger evaluator."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "highest_price", "current_price")
        high = float(inputs["highest_price"])
        current = float(inputs["current_price"])
        trail = float(inputs.get("trailing_stop_pct", 0.08))
        if high <= 0 or current <= 0 or not 0 < trail < 1:
            raise EngineInputError("prices must be positive and trail between 0 and 1")
        stop = high * (1 - trail)
        distance = (current - stop) / current
        return {
            "trailing_stop": round(stop, 8),
            "triggered": current <= stop,
            "approaching": 0 < distance <= float(inputs.get("warning_distance_pct", 0.02)),
            "distance_pct": round(distance, 8),
            "engine_version": self.engine_version,
        }
