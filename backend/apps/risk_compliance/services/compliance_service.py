from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.core.domain.enums import ComplianceDecision
from apps.orchestrator.models import AnalysisRun
from rules.compliance.policy_checker import PolicyChecker
from rules.compliance.restricted_list_checker import RestrictedListChecker
from rules.compliance.rule_evaluator import ComplianceRuleEvaluator

from ..models import ComplianceResult
from ..repositories import RiskComplianceRepository


class ComplianceService:
    def __init__(self, repository: RiskComplianceRepository | None = None) -> None:
        self.repository = repository or RiskComplianceRepository()

    @transaction.atomic
    def evaluate(self, run: AnalysisRun, context: dict[str, Any]) -> ComplianceResult:
        governance = run.run_manifest.get("governance", {})
        restricted_symbols = (
            {run.ticker.symbol} if governance.get("restricted_security") else set()
        )
        policies = (
            governance["compliance_policies"]
            if "compliance_policies" in governance
            else self.repository.active_policies()
        )
        evaluator = ComplianceRuleEvaluator(
            restricted_checker=RestrictedListChecker(restricted_symbols),
            policy_checker=PolicyChecker(policies),
        )
        result = evaluator.evaluate({"symbol": run.ticker.symbol, **context})
        restricted = result["decision"] == ComplianceDecision.RESTRICTED
        return ComplianceResult.objects.update_or_create(
            analysis_run=run,
            defaults={
                "decision": result["decision"],
                "passed": result["passed"],
                "restricted_list_match": restricted,
                "checks": result["checks"],
                "violations": result["violations"],
                "approval_required": result["approval_required"],
                "rule_version": result["rule_version"],
            },
        )[0]
