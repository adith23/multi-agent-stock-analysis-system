from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.core.domain.enums import RiskDecision
from apps.orchestrator.models import AnalysisRun
from rules.risk_limits.limit_checker import RiskLimitChecker

from ..models import RiskValidationResult
from ..repositories import RiskComplianceRepository


class RiskService:
    def __init__(self, repository: RiskComplianceRepository | None = None) -> None:
        self.repository = repository or RiskComplianceRepository()

    @transaction.atomic
    def validate(
        self,
        run: AnalysisRun,
        *,
        metrics: dict[str, Any],
        agent_output: dict[str, Any] | None = None,
    ) -> RiskValidationResult:
        limits = run.run_manifest.get("governance", {}).get("risk_limits")
        deterministic = RiskLimitChecker(limits or None).evaluate(metrics)
        agent_output = agent_output or {}
        decision = self._most_restrictive(
            str(deterministic["decision"]),
            str(agent_output.get("disposition", RiskDecision.PASS)),
        )
        breaches = [*deterministic["breaches"], *agent_output.get("limit_breaches", [])]
        mitigations = [*deterministic["mitigations"], *agent_output.get("mitigations", [])]
        return RiskValidationResult.objects.update_or_create(
            analysis_run=run,
            defaults={
                "decision": decision,
                "passed": decision in {RiskDecision.PASS, RiskDecision.PASS_WITH_WARNINGS},
                "risk_metrics": metrics,
                "breaches": breaches,
                "mitigations": mitigations,
                "hedge_suggestions": agent_output.get("hedge_suggestions", []),
                "scenario_results": agent_output.get("scenario_results", {}),
                "rationale": agent_output.get("rationale", "Deterministic risk-limit evaluation."),
                "requires_escalation": decision == RiskDecision.ESCALATE,
                "rule_version": deterministic["rule_version"],
                "agent_version": agent_output.get("metadata", {}).get("agent_version", ""),
                "model_version": agent_output.get("metadata", {}).get("model_name", ""),
                "prompt_version": agent_output.get("metadata", {}).get("prompt_version", ""),
            },
        )[0]

    @staticmethod
    def _most_restrictive(first: str, second: str) -> str:
        order = {
            RiskDecision.PASS: 0,
            RiskDecision.PASS_WITH_WARNINGS: 1,
            RiskDecision.HEDGE_REQUIRED: 2,
            RiskDecision.REDUCE_SIZE: 3,
            RiskDecision.ESCALATE: 4,
            RiskDecision.BLOCK: 5,
        }
        return str(max((RiskDecision(first), RiskDecision(second)), key=order.__getitem__))
