from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class DCFEngine(DeterministicEngine):
    """Unlevered free-cash-flow DCF with bear/base/bull scenarios."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(
            inputs,
            "base_free_cash_flow",
            "shares_outstanding",
            "net_debt",
            "wacc",
            "terminal_growth",
        )
        scenarios = inputs.get(
            "growth_scenarios",
            {
                "bear": float(inputs.get("growth_rate", 0.03)) - 0.02,
                "base": float(inputs.get("growth_rate", 0.03)),
                "bull": float(inputs.get("growth_rate", 0.03)) + 0.02,
            },
        )
        values = {
            name: self._scenario(inputs, float(growth)) for name, growth in scenarios.items()
        }
        if not {"bear", "base", "bull"} <= values.keys():
            raise EngineInputError("growth_scenarios must include bear, base, and bull")
        return {
            "methodology": "unlevered_dcf",
            "currency": inputs.get("currency", "USD"),
            "fair_value": values,
            "assumptions": {
                "wacc": float(inputs["wacc"]),
                "terminal_growth": float(inputs["terminal_growth"]),
                "projection_years": int(inputs.get("projection_years", 5)),
                "growth_scenarios": {key: float(value) for key, value in scenarios.items()},
            },
            "engine_version": self.engine_version,
        }

    def _scenario(self, inputs: dict[str, Any], growth: float) -> float:
        fcf = float(inputs["base_free_cash_flow"])
        shares = float(inputs["shares_outstanding"])
        net_debt = float(inputs["net_debt"])
        wacc = float(inputs["wacc"])
        terminal_growth = float(inputs["terminal_growth"])
        years = int(inputs.get("projection_years", 5))
        if fcf < 0 or shares <= 0 or years < 1:
            raise EngineInputError("FCF must be non-negative; shares and years must be positive")
        if not 0 <= terminal_growth < wacc < 1:
            raise EngineInputError("require 0 <= terminal_growth < wacc < 1")
        projected = np.array([fcf * (1 + growth) ** year for year in range(1, years + 1)])
        discounts = np.array([(1 + wacc) ** year for year in range(1, years + 1)])
        terminal = projected[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
        enterprise_value = float((projected / discounts).sum() + terminal / discounts[-1])
        return round((enterprise_value - net_debt) / shares, 8)
