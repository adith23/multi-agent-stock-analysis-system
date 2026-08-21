from __future__ import annotations

from typing import Any

from apps.core.domain.enums import ComplianceDecision
from rules.base import RuleEngine


class RestrictedListChecker(RuleEngine):
    def __init__(self, restricted_symbols: set[str] | frozenset[str] | None = None):
        self.restricted_symbols = frozenset(
            symbol.strip().upper() for symbol in (restricted_symbols or ())
        )

    def evaluate(self, context: dict[str, Any]) -> dict[str, Any]:
        symbol = str(context.get("symbol", "")).strip().upper()
        restricted = symbol in self.restricted_symbols
        return {
            "rule": "restricted_list",
            "symbol": symbol,
            "passed": not restricted,
            "decision": str(
                ComplianceDecision.RESTRICTED if restricted else ComplianceDecision.APPROVED
            ),
            "rule_version": self.rule_version,
        }
