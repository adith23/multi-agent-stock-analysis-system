from __future__ import annotations

from typing import Any

from apps.core.domain.enums import ActionSignal, AgentStance
from engines.exceptions import EngineInputError
from rules.base import RuleEngine


class ConvictionRules(RuleEngine):
    """Configurable FR-061/062 promotion thresholds."""

    DEFAULT_THRESHOLDS = {
        ActionSignal.STRONG_BUY: (85, 0.80, 3),
        ActionSignal.BUY: (65, 0.60, 2),
        ActionSignal.ACCUMULATE: (50, 0.50, 2),
        ActionSignal.STRONG_SELL: (85, 0.80, 3),
        ActionSignal.SELL: (65, 0.60, 2),
        ActionSignal.REDUCE: (50, 0.50, 2),
    }

    def __init__(
        self, thresholds: dict[ActionSignal | str, tuple[float, float, int]] | None = None
    ):
        self.thresholds = {
            ActionSignal(signal): values
            for signal, values in (thresholds or self.DEFAULT_THRESHOLDS).items()
        }

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        stances = {name: AgentStance(value) for name, value in context.get("stances", {}).items()}
        score = float(context.get("conviction_score", -1))
        if not stances or not 0 <= score <= 100:
            raise EngineInputError("stances and a 0-100 conviction_score are required")
        bullish = sum(value is AgentStance.BULLISH for value in stances.values())
        bearish = sum(value is AgentStance.BEARISH for value in stances.values())
        total = len(stances)
        signal = ActionSignal.HOLD
        if bullish > bearish:
            signal = self._promote(
                score,
                bullish / total,
                bullish,
                (ActionSignal.STRONG_BUY, ActionSignal.BUY, ActionSignal.ACCUMULATE),
            )
        elif bearish > bullish:
            signal = self._promote(
                score,
                bearish / total,
                bearish,
                (ActionSignal.STRONG_SELL, ActionSignal.SELL, ActionSignal.REDUCE),
            )
        level = {
            ActionSignal.STRONG_BUY: 5,
            ActionSignal.BUY: 4,
            ActionSignal.ACCUMULATE: 3,
            ActionSignal.HOLD: 2,
            ActionSignal.REDUCE: 3,
            ActionSignal.SELL: 4,
            ActionSignal.STRONG_SELL: 5,
        }[signal]
        return {
            "signal": str(signal),
            "conviction_score": score,
            "conviction_level": level,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": total - bullish - bearish,
            "aligned_ratio": round(max(bullish, bearish) / total, 8),
            "promotion_requirements_met": signal is not ActionSignal.HOLD,
            "rule_version": self.rule_version,
        }

    def _promote(
        self,
        score: float,
        ratio: float,
        count: int,
        candidates: tuple[ActionSignal, ...],
    ) -> ActionSignal:
        for signal in candidates:
            minimum_score, minimum_ratio, minimum_count = self.thresholds[signal]
            if score >= minimum_score and ratio >= minimum_ratio and count >= minimum_count:
                return signal
        return ActionSignal.HOLD

    def get_rules(self) -> list[dict[str, Any]]:
        return [
            {
                "signal": str(signal),
                "minimum_score": values[0],
                "minimum_aligned_ratio": values[1],
                "minimum_aligned_count": values[2],
            }
            for signal, values in self.thresholds.items()
        ]
