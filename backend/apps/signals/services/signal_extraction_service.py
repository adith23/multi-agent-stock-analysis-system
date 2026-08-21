from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.core.utils.hashing import content_hash
from apps.market_data.models import OHLCVBar, Ticker
from apps.signals.models import TechnicalSignal
from engines.technical import PatternEngine, TechnicalIndicatorEngine, TrendClassifier


class SignalExtractionService:
    """Application service bridging canonical OHLCV data to deterministic engines."""

    def __init__(
        self,
        *,
        indicator_engine: TechnicalIndicatorEngine | None = None,
        pattern_engine: PatternEngine | None = None,
        trend_classifier: TrendClassifier | None = None,
    ) -> None:
        self.indicator_engine = indicator_engine or TechnicalIndicatorEngine()
        self.pattern_engine = pattern_engine or PatternEngine()
        self.trend_classifier = trend_classifier or TrendClassifier()

    @transaction.atomic
    def extract_technical(
        self,
        ticker: Ticker,
        *,
        interval: str = "1d",
        limit: int = 252,
        as_of=None,
    ) -> dict[str, Any]:
        queryset = OHLCVBar.objects.filter(ticker=ticker, interval=interval)
        if as_of is not None:
            queryset = queryset.filter(timestamp__lte=as_of, available_at__lte=as_of)
        bars = list(queryset.order_by("-timestamp")[:limit])
        bars.reverse()
        data = [
            {
                "timestamp": bar.timestamp.isoformat(),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
            }
            for bar in bars
        ]
        indicators = self.indicator_engine.compute({"ohlcv": data})
        latest = indicators["latest"]
        patterns = self.pattern_engine.compute({"ohlcv": data, "atr": latest["atr_14"]})
        trend = self.trend_classifier.compute(
            {
                "current_price": data[-1]["close"],
                "sma_20": latest["sma_20"],
                "sma_50": latest["sma_50"],
                "rsi": latest["rsi_14"],
                "macd_histogram": latest["macd_histogram"],
            }
        )
        direction = {
            "uptrend": "bullish",
            "downtrend": "bearish",
        }.get(trend["trend_state"], "neutral")
        timestamp = bars[-1].timestamp
        source_hash = content_hash(
            {
                "ticker": ticker.symbol,
                "timestamp": timestamp,
                "interval": interval,
                "indicators": latest,
                "patterns": patterns,
                "trend": trend,
            }
        )
        signal, _ = TechnicalSignal.objects.update_or_create(
            ticker=ticker,
            signal_type="composite_technical",
            timeframe=interval,
            observed_at=timestamp,
            version=1,
            defaults={
                "value": trend["trend_score"],
                "direction": direction,
                "strength": min(abs(trend["trend_score"]) / 6, 1),
                "parameters": {
                    "indicators": latest,
                    "patterns": patterns,
                    "trend": trend,
                },
                "source_type": "deterministic_engine",
                "source_id": self.indicator_engine.engine_version,
                "source_timestamp": timestamp,
                "data_quality_score": min(bar.data_quality_score or 0 for bar in bars),
                "content_hash": source_hash,
                "model_version": self.indicator_engine.engine_version,
            },
        )
        return {
            "technical_signal_id": str(signal.id),
            "indicators": latest,
            "patterns": patterns,
            "trend": trend,
        }
