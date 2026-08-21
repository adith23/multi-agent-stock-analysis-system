from __future__ import annotations

from engines.position_sizing.base_sizer import SizingStrategy


class FixedFractionalSizer(SizingStrategy):
    def __init__(self, *, fraction: float = 0.02):
        if not 0 < fraction <= 1:
            raise ValueError("fraction must be between 0 and 1")
        self.fraction = fraction

    @property
    def methodology_name(self) -> str:
        return "fixed_fractional"

    def _weight(self, **context: float) -> float:
        return (
            self.fraction
            * context["risk_budget"]
            * context["conviction"]
            / 100
            * max(0.0, min(context["liquidity"], 1.0))
        )
