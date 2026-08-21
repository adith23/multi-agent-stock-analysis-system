from __future__ import annotations

from typing import Any

import pandas as pd

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class RelativeValueEngine(DeterministicEngine):
    """Rank target and peers across valuation, growth, quality, and momentum."""

    DEFAULT_DIRECTION = {
        "pe": -1,
        "ev_ebitda": -1,
        "price_to_book": -1,
        "revenue_growth": 1,
        "earnings_growth": 1,
        "roe": 1,
        "operating_margin": 1,
        "momentum": 1,
    }

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "companies", "target")
        frame = pd.DataFrame(inputs["companies"]).set_index("symbol")
        target = str(inputs["target"])
        if target not in frame.index or len(frame) < 2:
            raise EngineInputError("target and at least one peer are required")
        metrics = list(inputs.get("metrics", self.DEFAULT_DIRECTION))
        missing = set(metrics) - set(frame.columns)
        if missing:
            raise EngineInputError(f"peer data missing metrics: {', '.join(sorted(missing))}")
        directions = {**self.DEFAULT_DIRECTION, **inputs.get("directions", {})}
        weights = inputs.get("metric_weights", {})
        score = pd.Series(0.0, index=frame.index)
        details: dict[str, dict[str, float]] = {}
        total_weight = 0.0
        for metric in metrics:
            values = pd.to_numeric(frame[metric], errors="coerce")
            median = values.median()
            values = values.fillna(median)
            std = values.std(ddof=0)
            zscore = (values - values.mean()) / std if std else values * 0
            percentile = values.rank(pct=True)
            direction = float(directions.get(metric, 1))
            weight = float(weights.get(metric, 1))
            score += zscore * direction * weight
            total_weight += weight
            details[metric] = {
                "value": round(float(values.loc[target]), 6),
                "z_score": round(float(zscore.loc[target]), 6),
                "percentile": round(float(percentile.loc[target]), 6),
            }
        score /= max(total_weight, 1)
        ranking = score.rank(ascending=False, method="min").astype(int)
        ordered = sorted(
            (
                {
                    "symbol": symbol,
                    "composite_score": round(float(score.loc[symbol]), 6),
                    "rank": int(ranking.loc[symbol]),
                }
                for symbol in frame.index
            ),
            key=lambda item: item["rank"],
        )
        target_rank = int(ranking.loc[target])
        return {
            "target": target,
            "target_rank": target_rank,
            "peer_count": len(frame) - 1,
            "metric_details": details,
            "ranking": ordered,
            "preferred": target_rank == 1,
            "rationale": (
                "target leads the peer composite"
                if target_rank == 1
                else f"target ranks {target_rank} of {len(frame)}"
            ),
            "engine_version": self.engine_version,
        }
