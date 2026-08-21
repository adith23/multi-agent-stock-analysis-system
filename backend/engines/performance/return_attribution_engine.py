from __future__ import annotations

from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class ReturnAttributionEngine(DeterministicEngine):
    """Additive allocation and selection attribution by bucket."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(
            inputs,
            "portfolio_weights",
            "benchmark_weights",
            "portfolio_returns",
            "benchmark_returns",
        )
        keys = set(inputs["portfolio_weights"])
        if any(
            set(inputs[name]) != keys
            for name in (
                "benchmark_weights",
                "portfolio_returns",
                "benchmark_returns",
            )
        ):
            raise EngineInputError("all attribution mappings must share identical keys")
        benchmark_total = sum(
            float(inputs["benchmark_weights"][key]) * float(inputs["benchmark_returns"][key])
            for key in keys
        )
        rows = []
        for key in sorted(keys):
            portfolio_weight = float(inputs["portfolio_weights"][key])
            benchmark_weight = float(inputs["benchmark_weights"][key])
            portfolio_return = float(inputs["portfolio_returns"][key])
            benchmark_return = float(inputs["benchmark_returns"][key])
            allocation = (portfolio_weight - benchmark_weight) * (
                benchmark_return - benchmark_total
            )
            selection = benchmark_weight * (portfolio_return - benchmark_return)
            interaction = (portfolio_weight - benchmark_weight) * (
                portfolio_return - benchmark_return
            )
            rows.append(
                {
                    "bucket": key,
                    "allocation": round(allocation, 8),
                    "selection": round(selection, 8),
                    "interaction": round(interaction, 8),
                    "total": round(allocation + selection + interaction, 8),
                }
            )
        return {
            "attribution": rows,
            "total_active_return": round(sum(row["total"] for row in rows), 8),
            "engine_version": self.engine_version,
        }
