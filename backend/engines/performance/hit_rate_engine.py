from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine


class HitRateEngine(DeterministicEngine):
    """Recommendation hit rate and risk-adjusted outcome statistics."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "returns")
        returns = self.vector(inputs["returns"], name="returns")
        benchmark = np.asarray(
            inputs.get("benchmark_returns", np.zeros(len(returns))), dtype=float
        )
        if len(benchmark) != len(returns):
            from engines.exceptions import EngineInputError

            raise EngineInputError("benchmark_returns must match returns")
        active = returns - benchmark
        downside = returns[returns < 0]
        volatility = returns.std(ddof=1) if len(returns) > 1 else 0
        return {
            "observations": len(returns),
            "hit_rate": round(float((returns > 0).mean()), 8),
            "active_hit_rate": round(float((active > 0).mean()), 8),
            "average_return": round(float(returns.mean()), 8),
            "median_return": round(float(np.median(returns)), 8),
            "average_win": (
                round(float(returns[returns > 0].mean()), 8) if (returns > 0).any() else 0
            ),
            "average_loss": round(float(downside.mean()), 8) if len(downside) else 0,
            "sharpe_ratio": round(self.safe_divide(float(returns.mean()), float(volatility)), 8),
            "engine_version": self.engine_version,
        }
