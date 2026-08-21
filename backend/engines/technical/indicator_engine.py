from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class TechnicalIndicatorEngine(DeterministicEngine):
    """Compute FR-021 price, momentum, volatility, and volume indicators."""

    MINIMUM_BARS = 35

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        frame = self._frame(inputs)
        close = frame["close"]
        high = frame["high"]
        low = frame["low"]

        delta = close.diff()
        gains = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
        losses = -delta.clip(upper=0).ewm(alpha=1 / 14, adjust=False).mean()
        rs = gains / losses.replace(0, np.nan)
        rsi = (100 - 100 / (1 + rs)).fillna(100)

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        previous_close = close.shift(1)
        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = true_range.ewm(alpha=1 / 14, adjust=False).mean()
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std(ddof=0)

        output = frame.copy()
        output["sma_20"] = sma20
        output["sma_50"] = close.rolling(50, min_periods=min(50, len(close))).mean()
        output["ema_12"] = ema12
        output["ema_26"] = ema26
        output["rsi_14"] = rsi
        output["macd"] = macd
        output["macd_signal"] = macd_signal
        output["macd_histogram"] = macd - macd_signal
        output["atr_14"] = atr
        output["bollinger_upper"] = sma20 + 2 * std20
        output["bollinger_middle"] = sma20
        output["bollinger_lower"] = sma20 - 2 * std20
        output["volume_sma_20"] = frame["volume"].rolling(20).mean()
        output["annualized_volatility_20"] = close.pct_change().rolling(20).std() * np.sqrt(252)

        latest = output.iloc[-1]
        fields = (
            "sma_20",
            "sma_50",
            "ema_12",
            "ema_26",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_histogram",
            "atr_14",
            "bollinger_upper",
            "bollinger_middle",
            "bollinger_lower",
            "volume_sma_20",
            "annualized_volatility_20",
        )
        return {
            "latest": {
                field: None if pd.isna(latest[field]) else round(float(latest[field]), 8)
                for field in fields
            },
            "series": output.replace({np.nan: None}).to_dict(orient="records"),
            "observations": len(output),
            "engine_version": self.engine_version,
        }

    def _frame(self, inputs: dict[str, Any]) -> pd.DataFrame:
        self.require(inputs, "ohlcv")
        frame = pd.DataFrame(inputs["ohlcv"]).copy()
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(frame.columns)
        if missing:
            raise EngineInputError(f"OHLCV missing columns: {', '.join(sorted(missing))}")
        if len(frame) < self.MINIMUM_BARS:
            from engines.exceptions import InsufficientDataError

            raise InsufficientDataError(
                f"technical indicators require at least {self.MINIMUM_BARS} bars"
            )
        for column in required:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        if (frame[["open", "high", "low", "close", "volume"]] < 0).any().any():
            raise EngineInputError("OHLCV values cannot be negative")
        if (frame["high"] < frame["low"]).any():
            raise EngineInputError("OHLCV high cannot be below low")
        return frame.reset_index(drop=True)
