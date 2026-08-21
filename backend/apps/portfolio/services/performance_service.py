from __future__ import annotations

from datetime import timedelta
from statistics import stdev
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.domain.enums import ActionSignal
from apps.market_data.models import BarInterval, OHLCVBar, Ticker
from engines.performance.hit_rate_engine import HitRateEngine
from engines.performance.signal_decay_engine import SignalDecayEngine

from ..models import PerformanceAttributionRecord
from ..repositories import PortfolioRepository


class PerformanceService:
    """Point-in-time recommendation outcome measurement and attribution."""

    DEFAULT_PERIODS = {"1d": 1, "5d": 5, "20d": 20, "60d": 60}

    def __init__(
        self,
        repository: PortfolioRepository | None = None,
        *,
        periods: dict[str, int] | None = None,
    ) -> None:
        self.repository = repository or PortfolioRepository()
        self.periods = periods or getattr(
            settings,
            "PERFORMANCE_MEASUREMENT_PERIODS",
            self.DEFAULT_PERIODS,
        )

    @transaction.atomic
    def track_due(self, *, as_of=None) -> dict[str, int]:
        as_of = as_of or timezone.now()
        checked = created = 0
        for recommendation in self.repository.approved_recommendations():
            checked += 1
            entry_at = recommendation.reviewed_at or recommendation.created_at
            entry = self._first_bar_at_or_after(recommendation.ticker, entry_at)
            if entry is None:
                continue
            for label, days in self.periods.items():
                due_at = entry.timestamp + timedelta(days=int(days))
                if due_at > as_of:
                    continue
                exit_bar = self._first_bar_at_or_after(
                    recommendation.ticker,
                    due_at,
                    upper_bound=as_of,
                )
                if exit_bar is None:
                    continue
                _, was_created = self._persist_measurement(
                    recommendation,
                    period=label,
                    entry=entry,
                    exit_bar=exit_bar,
                )
                created += int(was_created)
            self._refresh_decay(recommendation)
        return {"checked": checked, "created": created}

    def _persist_measurement(self, recommendation, *, period: str, entry, exit_bar):
        entry_price = self._price(entry)
        exit_price = self._price(exit_bar)
        asset_return = float((exit_price - entry_price) / entry_price)
        signal_return = self._signal_return(recommendation.action, asset_return)
        benchmark_return = self._benchmark_return(
            recommendation,
            entry.timestamp,
            exit_bar.timestamp,
        )
        active_return = signal_return - benchmark_return
        risk_adjusted = self._risk_adjusted_return(
            recommendation.ticker,
            entry.timestamp,
            exit_bar.timestamp,
            signal_return,
        )
        return PerformanceAttributionRecord.objects.update_or_create(
            recommendation=recommendation,
            measurement_period=period,
            version=1,
            defaults={
                "period_start": entry.timestamp,
                "period_end": exit_bar.timestamp,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "realized_return": signal_return,
                "benchmark_return": benchmark_return,
                "excess_return": active_return,
                "hit": signal_return > 0,
                "risk_adjusted_return": risk_adjusted,
                "agent_attribution": self._agent_attribution(
                    recommendation,
                    asset_return,
                ),
            },
        )

    @staticmethod
    def _first_bar_at_or_after(ticker, timestamp, *, upper_bound=None):
        queryset = OHLCVBar.objects.filter(
            ticker=ticker,
            interval=BarInterval.DAY_1,
            timestamp__gte=timestamp,
        )
        if upper_bound is not None:
            queryset = queryset.filter(timestamp__lte=upper_bound)
        return queryset.order_by("timestamp").first()

    @staticmethod
    def _last_bar_at_or_before(ticker, timestamp, *, lower_bound=None):
        queryset = OHLCVBar.objects.filter(
            ticker=ticker,
            interval=BarInterval.DAY_1,
            timestamp__lte=timestamp,
        )
        if lower_bound is not None:
            queryset = queryset.filter(timestamp__gte=lower_bound)
        return queryset.order_by("-timestamp").first()

    @staticmethod
    def _price(bar):
        return bar.adjusted_close if bar.adjusted_close is not None else bar.close

    @staticmethod
    def _signal_return(action: str, asset_return: float) -> float:
        signal = ActionSignal(action)
        if signal in ActionSignal.bullish_signals():
            return asset_return
        if signal in ActionSignal.bearish_signals():
            return -asset_return
        hold_tolerance = float(getattr(settings, "PERFORMANCE_HOLD_TOLERANCE", 0.03))
        return hold_tolerance - abs(asset_return)

    def _benchmark_return(self, recommendation, start, end) -> float:
        config = recommendation.analysis_run.analysis_config
        symbol = config.get("performance_benchmark_symbol")
        if not symbol:
            return 0.0
        benchmark = (
            Ticker.objects.active()
            .for_symbol(str(symbol), config.get("performance_benchmark_exchange"))
            .first()
        )
        if benchmark is None:
            return 0.0
        entry = self._first_bar_at_or_after(benchmark, start, upper_bound=end)
        exit_bar = self._last_bar_at_or_before(benchmark, end, lower_bound=start)
        if entry is None or exit_bar is None:
            return 0.0
        entry_price = self._price(entry)
        raw_return = float((self._price(exit_bar) - entry_price) / entry_price)
        return self._signal_return(recommendation.action, raw_return)

    def _risk_adjusted_return(self, ticker, start, end, signal_return: float) -> float | None:
        bars = list(
            OHLCVBar.objects.filter(
                ticker=ticker,
                interval=BarInterval.DAY_1,
                timestamp__range=(start, end),
            ).order_by("timestamp")
        )
        prices = [float(self._price(bar)) for bar in bars]
        if len(prices) < 3:
            return None
        returns = [
            (current - previous) / previous
            for previous, current in zip(prices, prices[1:], strict=False)
            if previous > 0
        ]
        volatility = stdev(returns) * (252**0.5) if len(returns) >= 2 else 0.0
        return signal_return / volatility if volatility > 0 else None

    @staticmethod
    def _agent_attribution(recommendation, asset_return: float) -> dict[str, Any]:
        realized_direction = (
            "bullish" if asset_return > 0 else "bearish" if asset_return < 0 else "neutral"
        )
        attribution = {}
        for report in recommendation.analysis_run.specialist_reports.all():
            aligned = report.stance == realized_direction
            attribution[report.specialist_type] = {
                "stance": report.stance,
                "confidence": report.confidence,
                "aligned": aligned,
                "contribution": report.confidence * (1 if aligned else -1),
            }
        return attribution

    @staticmethod
    def _refresh_decay(recommendation) -> None:
        records = list(
            recommendation.performance_records.order_by("period_end").only(
                "measurement_period",
                "realized_return",
            )
        )
        if len(records) < 3:
            return
        horizons = []
        returns = []
        for record in records:
            digits = "".join(
                character for character in record.measurement_period if character.isdigit()
            )
            if not digits:
                continue
            horizons.append(int(digits))
            returns.append(record.realized_return)
        if len(horizons) < 3:
            return
        decay = SignalDecayEngine().compute(
            {
                "horizons": horizons,
                "mean_returns": returns,
                "minimum_half_life": getattr(
                    settings,
                    "PERFORMANCE_MINIMUM_HALF_LIFE_DAYS",
                    5,
                ),
            }
        )
        recommendation.performance_records.update(signal_decay=decay)

    @staticmethod
    def summary(*, queryset=None) -> dict[str, Any]:
        queryset = queryset if queryset is not None else PerformanceAttributionRecord.objects.all()
        records = list(
            queryset.order_by("period_end").values(
                "realized_return",
                "benchmark_return",
                "signal_decay",
            )
        )
        if not records:
            return {
                "observations": 0,
                "hit_rate": None,
                "average_return": None,
                "average_excess_return": None,
                "recalibration_recommended": False,
            }
        metrics = HitRateEngine().compute(
            {
                "returns": [item["realized_return"] for item in records],
                "benchmark_returns": [item["benchmark_return"] for item in records],
            }
        )
        threshold = float(getattr(settings, "PERFORMANCE_MINIMUM_HIT_RATE", 0.45))
        return {
            **metrics,
            "average_excess_return": sum(
                item["realized_return"] - item["benchmark_return"] for item in records
            )
            / len(records),
            "recalibration_recommended": metrics["hit_rate"] < threshold
            or any(
                item["signal_decay"].get("recalibration_recommended", False) for item in records
            ),
        }
