from __future__ import annotations

from engines.position_sizing.base_sizer import SizingStrategy


class RiskParitySizer(SizingStrategy):
    @property
    def methodology_name(self) -> str:
        return "inverse_volatility_risk_parity"

    def _weight(self, **context: float) -> float:
        if context["volatility"] <= 0:
            return 0.0
        return (
            context["risk_budget"]
            / context["volatility"]
            * context["conviction"]
            / 100
            * max(0.0, min(context["liquidity"], 1.0))
        )
