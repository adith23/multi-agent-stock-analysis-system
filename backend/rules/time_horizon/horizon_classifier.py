from __future__ import annotations

from typing import Any

from apps.core.domain.enums import TimeHorizon
from engines.exceptions import EngineInputError
from rules.base import RuleEngine


class TimeHorizonClassifier(RuleEngine):
    """Map the primary signal driver and catalyst timing to FR-065 horizons."""

    DRIVER_DEFAULTS = {
        "technical": TimeHorizon.TACTICAL,
        "event": TimeHorizon.TACTICAL,
        "sentiment": TimeHorizon.TACTICAL,
        "earnings": TimeHorizon.MEDIUM_TERM,
        "valuation": TimeHorizon.MEDIUM_TERM,
        "fundamental": TimeHorizon.STRATEGIC,
        "macro": TimeHorizon.STRATEGIC,
        "structural": TimeHorizon.STRATEGIC,
    }

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        driver = str(context.get("primary_driver", "")).casefold()
        if driver not in self.DRIVER_DEFAULTS:
            raise EngineInputError(f"unsupported primary driver: {driver!r}")
        days = context.get("catalyst_days")
        horizon = self.DRIVER_DEFAULTS[driver]
        if days is not None:
            days = int(days)
            if days <= 30:
                horizon = TimeHorizon.TACTICAL
            elif days <= 183:
                horizon = TimeHorizon.MEDIUM_TERM
            else:
                horizon = TimeHorizon.STRATEGIC
        configuration = {
            TimeHorizon.TACTICAL: {
                "maximum_days": 30,
                "review_frequency_days": 5,
                "risk_multiplier": 0.75,
                "exit_style": "tight_technical",
            },
            TimeHorizon.MEDIUM_TERM: {
                "maximum_days": 183,
                "review_frequency_days": 21,
                "risk_multiplier": 1.0,
                "exit_style": "catalyst_and_atr",
            },
            TimeHorizon.STRATEGIC: {
                "maximum_days": 730,
                "review_frequency_days": 90,
                "risk_multiplier": 1.25,
                "exit_style": "thesis_invalidation",
            },
        }[horizon]
        return {
            "horizon": str(horizon),
            "primary_driver": driver,
            **configuration,
            "rule_version": self.rule_version,
        }
