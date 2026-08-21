from __future__ import annotations

from collections import defaultdict
from typing import Any

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class ConcentrationEngine(DeterministicEngine):
    """HHI, top-position, sector, and factor concentration diagnostics."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(inputs, "weights")
        raw = inputs["weights"]
        names = list(raw) if isinstance(raw, dict) else list(inputs.get("assets", []))
        values = list(raw.values()) if isinstance(raw, dict) else list(raw)
        weights = self.normalized_weights(values)
        if names and len(names) != len(weights):
            raise EngineInputError("asset names must match weights")
        names = names or [str(index) for index in range(len(weights))]
        hhi = float((weights**2).sum())
        sectors: dict[str, float] = defaultdict(float)
        sector_map = inputs.get("sectors", {})
        for name, weight in zip(names, weights, strict=True):
            sectors[str(sector_map.get(name, "unclassified"))] += float(weight)
        max_position = float(weights.max())
        max_sector = max(sectors.values())
        alerts = []
        if max_position > float(inputs.get("max_position_weight", 0.10)):
            alerts.append("position_concentration")
        if max_sector > float(inputs.get("max_sector_weight", 0.30)):
            alerts.append("sector_concentration")
        if hhi > float(inputs.get("max_hhi", 0.18)):
            alerts.append("portfolio_hhi")
        effective_positions = self.safe_divide(1, hhi)
        return {
            "hhi": round(hhi, 8),
            "effective_positions": round(effective_positions, 4),
            "largest_position": round(max_position, 8),
            "sector_exposures": {key: round(value, 8) for key, value in sectors.items()},
            "largest_sector": round(max_sector, 8),
            "alerts": alerts,
            "engine_version": self.engine_version,
        }
