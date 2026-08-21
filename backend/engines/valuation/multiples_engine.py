from __future__ import annotations

from typing import Any

import numpy as np

from engines.base import DeterministicEngine
from engines.exceptions import EngineInputError


class MultiplesValuationEngine(DeterministicEngine):
    """Triangulate per-share fair value from peer P/E and EV/EBITDA."""

    def compute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        self.require(
            inputs, "peer_pe", "peer_ev_ebitda", "eps", "ebitda", "net_debt", "shares_outstanding"
        )
        pe = self.vector(inputs["peer_pe"], name="peer_pe")
        ev_ebitda = self.vector(inputs["peer_ev_ebitda"], name="peer_ev_ebitda")
        pe = pe[pe > 0]
        ev_ebitda = ev_ebitda[ev_ebitda > 0]
        if not len(pe) or not len(ev_ebitda):
            raise EngineInputError("peer multiples require positive observations")
        shares = float(inputs["shares_outstanding"])
        if shares <= 0:
            raise EngineInputError("shares_outstanding must be positive")
        pe_value = float(inputs["eps"]) * float(np.median(pe))
        ev_value = (
            float(inputs["ebitda"]) * float(np.median(ev_ebitda)) - float(inputs["net_debt"])
        ) / shares
        blended = pe_value * float(inputs.get("pe_weight", 0.5)) + ev_value * (
            1 - float(inputs.get("pe_weight", 0.5))
        )
        return {
            "methodology": "peer_multiples",
            "pe_fair_value": round(pe_value, 8),
            "ev_ebitda_fair_value": round(ev_value, 8),
            "blended_fair_value": round(blended, 8),
            "peer_medians": {
                "pe": round(float(np.median(pe)), 6),
                "ev_ebitda": round(float(np.median(ev_ebitda)), 6),
            },
            "engine_version": self.engine_version,
        }
