from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class DividendDiscountEngine(DeterministicEngine):
    """Gordon Growth dividend-discount valuation."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "dividend_per_share", "required_return", "growth_rate")
        dividend = float(inputs["dividend_per_share"])
        required = float(inputs["required_return"])
        growth = float(inputs["growth_rate"])
        if dividend < 0 or not 0 <= growth < required < 1:
            raise EngineInputError(
                "dividend must be non-negative and 0 <= growth < required_return < 1"
            )
        next_dividend = dividend * (1 + growth)
        value = next_dividend / (required - growth)
        return {
            "methodology": "gordon_growth_ddm",
            "fair_value": round(value, 8),
            "next_dividend": round(next_dividend, 8),
            "required_return": required,
            "growth_rate": growth,
            "engine_version": self.engine_version,
        }
