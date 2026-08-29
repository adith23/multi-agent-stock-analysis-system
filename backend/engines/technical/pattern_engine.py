from __future__ import annotations

from typing import Any

import pandas as pd

from engines.base import DeterministicEngine
from engines.exceptions import InsufficientDataError


class PatternEngine(DeterministicEngine):
    """Detect support/resistance, gaps, breakouts, breakdowns, and reversals."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "ohlcv")
        frame = pd.DataFrame(inputs["ohlcv"]).copy()
        for col in ("open", "high", "low", "close", "volume"):
            if col in frame.columns:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
        lookback = int(inputs.get("lookback", 20))
        if len(frame) <= lookback:
            raise InsufficientDataError(f"patterns require more than {lookback} bars")
        recent = frame.iloc[-(lookback + 1) : -1]
        latest = frame.iloc[-1]
        resistance = float(recent["high"].max())
        support = float(recent["low"].min())
        close = float(latest["close"])
        previous_close = float(frame.iloc[-2]["close"])
        atr = float(inputs.get("atr", (recent["high"] - recent["low"]).mean()))
        volume_average = float(recent["volume"].mean())
        volume_ratio = self.safe_divide(float(latest["volume"]), volume_average)

        gap_pct = self.safe_divide(float(latest["open"]) - previous_close, previous_close)
        breakout = close > resistance and volume_ratio >= 1.2
        breakdown = close < support and volume_ratio >= 1.2
        body = abs(close - float(latest["open"]))
        full_range = max(float(latest["high"]) - float(latest["low"]), 1e-12)
        exhaustion = volume_ratio >= 2 and body / full_range < 0.3
        reversal = (float(latest["low"]) < support and close > support) or (
            float(latest["high"]) > resistance and close < resistance
        )
        return {
            "support": round(support, 8),
            "resistance": round(resistance, 8),
            "breakout": breakout,
            "breakdown": breakdown,
            "exhaustion": exhaustion,
            "reversal": reversal,
            "gap": abs(gap_pct) >= float(inputs.get("gap_threshold", 0.02)),
            "gap_pct": round(gap_pct, 6),
            "distance_to_support_atr": round(self.safe_divide(close - support, atr), 4),
            "distance_to_resistance_atr": round(self.safe_divide(resistance - close, atr), 4),
            "volume_ratio": round(volume_ratio, 4),
            "engine_version": self.engine_version,
        }
