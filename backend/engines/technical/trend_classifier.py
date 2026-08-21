from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine


class TrendClassifier(DeterministicEngine):
    """Rule-based multi-timeframe trend state and timing cues."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "current_price", "sma_20", "sma_50", "rsi", "macd_histogram")
        price = float(inputs["current_price"])
        sma20 = float(inputs["sma_20"])
        sma50 = float(inputs["sma_50"])
        rsi = float(inputs["rsi"])
        histogram = float(inputs["macd_histogram"])

        score = 0
        score += 2 if price > sma20 else -2
        score += 2 if sma20 > sma50 else -2
        score += 1 if histogram > 0 else -1
        score += 1 if rsi >= 55 else (-1 if rsi <= 45 else 0)
        if score >= 4:
            state = "uptrend"
        elif score <= -4:
            state = "downtrend"
        elif abs(score) <= 1:
            state = "sideways"
        else:
            state = "transitioning"
        cue = (
            "enter"
            if state == "uptrend" and rsi < 75
            else ("exit" if state == "downtrend" and rsi > 25 else "wait")
        )
        return {
            "trend_state": state,
            "trend_score": score,
            "timing_cue": cue,
            "momentum_state": (
                "overbought" if rsi >= 70 else ("oversold" if rsi <= 30 else "balanced")
            ),
            "engine_version": self.engine_version,
        }
