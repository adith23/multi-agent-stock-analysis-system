from __future__ import annotations

from typing import Any

from apps.core.domain.enums import ComplianceDecision
from rules.base import RuleEngine

from .policy_checker import PolicyChecker
from .restricted_list_checker import RestrictedListChecker


class ComplianceRuleEvaluator(RuleEngine):
    """Composite compliance control; blocking rules cannot be overridden here."""

    def __init__(
        self,
        *,
        restricted_checker: RestrictedListChecker | None = None,
        policy_checker: PolicyChecker | None = None,
    ) -> None:
        self.restricted_checker = restricted_checker or RestrictedListChecker()
        self.policy_checker = policy_checker or PolicyChecker()

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        restricted = self.restricted_checker.evaluate(context)
        policies = self.policy_checker.evaluate(context)
        if not restricted["passed"]:
            decision = ComplianceDecision.RESTRICTED
        elif policies["blocked"]:
            decision = ComplianceDecision.VIOLATED
        elif policies["requires_approval"]:
            decision = ComplianceDecision.REQUIRES_APPROVAL
        else:
            decision = ComplianceDecision.APPROVED
        return {
            "decision": str(decision),
            "passed": decision is ComplianceDecision.APPROVED,
            "checks": [restricted, policies],
            "violations": policies["violations"],
            "approval_required": decision is ComplianceDecision.REQUIRES_APPROVAL,
            "rule_version": self.rule_version,
        }
