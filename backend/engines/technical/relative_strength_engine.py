from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine


class RelativeStrengthEngine(DeterministicEngine):
    """Compare cumulative and risk-adjusted performance with a benchmark."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "asset_prices", "benchmark_prices")
        asset = self.vector(inputs["asset_prices"], name="asset_prices", minimum_length=3)
        benchmark = self.vector(
            inputs["benchmark_prices"], name="benchmark_prices", minimum_length=3
        )
        length = min(len(asset), len(benchmark))
        asset, benchmark = asset[-length:], benchmark[-length:]
        asset_returns = np.diff(asset) / asset[:-1]
        benchmark_returns = np.diff(benchmark) / benchmark[:-1]
        active = asset_returns - benchmark_returns
        cumulative_asset = asset[-1] / asset[0] - 1
        cumulative_benchmark = benchmark[-1] / benchmark[0] - 1
        tracking_error = active.std(ddof=1) * np.sqrt(252) if len(active) > 1 else 0
        information_ratio = self.safe_divide(active.mean() * 252, tracking_error)
        return {
            "asset_return": round(float(cumulative_asset), 8),
            "benchmark_return": round(float(cumulative_benchmark), 8),
            "relative_return": round(float(cumulative_asset - cumulative_benchmark), 8),
            "information_ratio": round(information_ratio, 6),
            "trend": (
                "outperforming"
                if active[-min(20, len(active)) :].mean() > 0
                else "underperforming"
            ),
            "score": round(float(np.clip(50 + information_ratio * 10, 0, 100)), 2),
            "engine_version": self.engine_version,
        }
