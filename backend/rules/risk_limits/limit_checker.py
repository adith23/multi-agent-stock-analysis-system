from __future__ import annotations

from typing import Any

from apps.core.domain.enums import RiskDecision
from rules.base import RuleEngine


class RiskLimitChecker(RuleEngine):
    """Hard/soft portfolio limit enforcement with block and escalation authority."""

    DEFAULT_LIMITS = {
        "position_weight": {"maximum": 0.10, "severity": "block"},
        "sector_weight": {"maximum": 0.30, "severity": "block"},
        "gross_leverage": {"maximum": 1.50, "severity": "block"},
        "portfolio_var": {"maximum": 0.05, "severity": "escalate"},
        "days_to_liquidate": {"maximum": 5.0, "severity": "reduce"},
        "pairwise_correlation": {"maximum": 0.85, "severity": "warning"},
    }

    def __init__(self, limits: dict[str, dict[str, Any]] | None = None):
        self.limits = limits or self.DEFAULT_LIMITS

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        breaches = []
        for metric, limit in self.limits.items():
            if metric not in context:
                continue
            actual = float(context[metric])
            maximum = float(limit["maximum"])
            if actual > maximum:
                breaches.append(
                    {
                        "metric": metric,
                        "actual": actual,
                        "maximum": maximum,
                        "severity": limit.get("severity", "block"),
                    }
                )
        severities = {item["severity"] for item in breaches}
        if "block" in severities:
            decision = RiskDecision.BLOCK
        elif "escalate" in severities:
            decision = RiskDecision.ESCALATE
        elif "reduce" in severities:
            decision = RiskDecision.REDUCE_SIZE
        elif breaches:
            decision = RiskDecision.PASS_WITH_WARNINGS
        else:
            decision = RiskDecision.PASS
        return {
            "decision": str(decision),
            "passed": decision in {RiskDecision.PASS, RiskDecision.PASS_WITH_WARNINGS},
            "breaches": breaches,
            "mitigations": [
                self._mitigation(item["severity"], item["metric"]) for item in breaches
            ],
            "rule_version": self.rule_version,
        }

    @staticmethod
    def _mitigation(severity: str, metric: str) -> str:
        action = {
            "block": "reject_trade",
            "escalate": "mandatory_risk_review",
            "reduce": "reduce_position_size",
            "warning": "monitor_exposure",
        }.get(severity, "review")
        return f"{action}:{metric}"

    def get_rules(self) -> list[dict[str, Any]]:
        return [
            {"metric": metric, **configuration} for metric, configuration in self.limits.items()
        ]
