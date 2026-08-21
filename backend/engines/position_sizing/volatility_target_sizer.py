from __future__ import annotations

from engines.position_sizing.base_sizer import SizingStrategy


class VolatilityTargetSizer(SizingStrategy):
    def __init__(self, *, target_volatility: float = 0.10):
        if target_volatility <= 0:
            raise ValueError("target_volatility must be positive")
        self.target_volatility = target_volatility

    @property
    def methodology_name(self) -> str:
        return "volatility_target"

    def _weight(self, **context: float) -> float:
        if context["volatility"] <= 0:
            return 0.0
        correlation_penalty = max(0.0, 1 - max(0.0, context["correlation"]))
        return (
            self.target_volatility
            / context["volatility"]
            * context["risk_budget"]
            * correlation_penalty
            * context["conviction"]
            / 100
        )
