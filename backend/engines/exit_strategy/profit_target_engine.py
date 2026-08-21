from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class ProfitTargetEngine(DeterministicEngine):
    """Produce R-multiple targets from entry and protective stop."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "entry_price", "stop_price")
        entry = float(inputs["entry_price"])
        stop = float(inputs["stop_price"])
        if not 0 < stop < entry:
            raise EngineInputError("require 0 < stop_price < entry_price")
        risk = entry - stop
        multiples = tuple(float(value) for value in inputs.get("r_multiples", (1, 2, 3)))
        if any(value <= 0 for value in multiples):
            raise EngineInputError("R multiples must be positive")
        targets = [
            {
                "r_multiple": multiple,
                "price": round(entry + risk * multiple, 8),
                "return_pct": round(risk * multiple / entry, 8),
            }
            for multiple in multiples
        ]
        return {
            "risk_per_share": round(risk, 8),
            "targets": targets,
            "engine_version": self.engine_version,
        }
