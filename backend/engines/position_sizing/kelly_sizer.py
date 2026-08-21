from __future__ import annotations

from engines.position_sizing.base_sizer import SizingStrategy


class KellySizer(SizingStrategy):
    def __init__(self, *, win_probability: float, payoff_ratio: float, fraction: float = 0.5):
        if not 0 <= win_probability <= 1 or payoff_ratio <= 0 or not 0 < fraction <= 1:
            raise ValueError("invalid Kelly parameters")
        self.win_probability = win_probability
        self.payoff_ratio = payoff_ratio
        self.fraction = fraction

    @property
    def methodology_name(self) -> str:
        return "fractional_kelly"

    def _weight(self, **context: float) -> float:
        kelly = self.win_probability - (1 - self.win_probability) / self.payoff_ratio
        conviction_scale = context["conviction"] / 100
        liquidity_scale = max(0.0, min(context["liquidity"], 1.0))
        return max(0.0, kelly) * self.fraction * conviction_scale * liquidity_scale
