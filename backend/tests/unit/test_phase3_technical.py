from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from engines.exceptions import EngineInputError, InsufficientDataError
from engines.technical import (
    PatternEngine,
    RelativeStrengthEngine,
    TechnicalIndicatorEngine,
    TrendClassifier,
)


def sample_ohlcv(count: int = 60) -> list[dict]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        {
            "timestamp": (start + timedelta(days=index)).isoformat(),
            "open": 100 + index * 0.5,
            "high": 102 + index * 0.5,
            "low": 99 + index * 0.5,
            "close": 101 + index * 0.5,
            "volume": 1_000_000 + index * 10_000,
        }
        for index in range(count)
    ]


def test_indicator_engine_computes_complete_dashboard() -> None:
    result = TechnicalIndicatorEngine().compute({"ohlcv": sample_ohlcv()})

    assert result["observations"] == 60
    assert result["latest"]["rsi_14"] == 100
    assert result["latest"]["sma_20"] is not None
    assert result["latest"]["macd"] > 0
    assert len(result["series"]) == 60


def test_indicator_engine_enforces_minimum_data_and_ranges() -> None:
    with pytest.raises(InsufficientDataError):
        TechnicalIndicatorEngine().compute({"ohlcv": sample_ohlcv(10)})
    invalid = sample_ohlcv()
    invalid[-1]["high"] = invalid[-1]["low"] - 1
    with pytest.raises(EngineInputError, match="high"):
        TechnicalIndicatorEngine().compute({"ohlcv": invalid})


def test_pattern_and_trend_classification() -> None:
    bars = sample_ohlcv()
    bars[-1]["close"] = bars[-2]["high"] + 10
    bars[-1]["high"] = bars[-1]["close"] + 1
    bars[-1]["volume"] *= 3
    pattern = PatternEngine().compute({"ohlcv": bars, "atr": 2})
    trend = TrendClassifier().compute(
        {
            "current_price": 130,
            "sma_20": 125,
            "sma_50": 115,
            "rsi": 60,
            "macd_histogram": 1,
        }
    )

    assert pattern["breakout"] is True
    assert pattern["volume_ratio"] > 1.2
    assert trend["trend_state"] == "uptrend"
    assert trend["timing_cue"] == "enter"


def test_relative_strength_compares_aligned_price_history() -> None:
    asset = np.linspace(100, 140, 60)
    benchmark = np.linspace(100, 110, 60)

    result = RelativeStrengthEngine().compute(
        {"asset_prices": asset, "benchmark_prices": benchmark}
    )

    assert result["relative_return"] > 0
    assert result["trend"] == "outperforming"
    assert result["score"] > 50
