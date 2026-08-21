from __future__ import annotations

import operator
from typing import Any

from engines.exceptions import EngineInputError
from rules.base import RuleEngine


class PolicyChecker(RuleEngine):
    OPERATORS = {
        "eq": operator.eq,
        "ne": operator.ne,
        "lt": operator.lt,
        "lte": operator.le,
        "gt": operator.gt,
        "gte": operator.ge,
        "in": lambda value, expected: value in expected,
        "not_in": lambda value, expected: value not in expected,
    }

    def __init__(self, policies: list[dict[str, Any]] | None = None):
        self.policies = list(policies or [])

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        violations = []
        for policy in self.policies:
            operation = self.OPERATORS.get(policy.get("operator"))
            if operation is None:
                raise EngineInputError(f"unsupported policy operator: {policy.get('operator')}")
            actual = context.get(policy["field"])
            passed = operation(actual, policy["value"])
            if not passed:
                violations.append(
                    {
                        "policy_id": policy["id"],
                        "field": policy["field"],
                        "actual": actual,
                        "expected": policy["value"],
                        "severity": policy.get("severity", "block"),
                    }
                )
        return {
            "passed": not violations,
            "violations": violations,
            "requires_approval": any(item["severity"] == "approval" for item in violations),
            "blocked": any(item["severity"] == "block" for item in violations),
            "rule_version": self.rule_version,
        }

    def get_rules(self) -> list[dict[str, Any]]:
        return self.policies
