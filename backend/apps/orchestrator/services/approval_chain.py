from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from apps.core.domain.enums import ComplianceDecision, RiskDecision
from apps.orchestrator.models import AnalysisRun


class GateDecision(StrEnum):
    PASS = "pass"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass(frozen=True, slots=True)
class GateOutcome:
    decision: GateDecision
    gate: str
    rationale: str


class RiskGate:
    def evaluate(self, run: AnalysisRun) -> GateOutcome:
        result = run.risk_validation
        if result.decision == RiskDecision.BLOCK:
            return GateOutcome(GateDecision.BLOCK, "risk", result.rationale)
        if result.decision == RiskDecision.ESCALATE:
            return GateOutcome(GateDecision.ESCALATE, "risk", result.rationale)
        return GateOutcome(GateDecision.PASS, "risk", result.rationale)


class ComplianceGate:
    def evaluate(self, run: AnalysisRun) -> GateOutcome:
        result = run.compliance_result
        if result.decision in {ComplianceDecision.RESTRICTED, ComplianceDecision.VIOLATED}:
            return GateOutcome(GateDecision.BLOCK, "compliance", "Binding compliance violation.")
        if result.decision in {
            ComplianceDecision.REQUIRES_APPROVAL,
            ComplianceDecision.ESCALATED,
        }:
            return GateOutcome(
                GateDecision.ESCALATE,
                "compliance",
                "Compliance approval is required.",
            )
        return GateOutcome(GateDecision.PASS, "compliance", "Compliance checks passed.")


class ApprovalChain:
    """Chain of Responsibility: risk -> compliance -> PM review."""

    def evaluate(self, run: AnalysisRun) -> GateOutcome:
        for gate in (RiskGate(), ComplianceGate()):
            outcome = gate.evaluate(run)
            if outcome.decision is not GateDecision.PASS:
                return outcome
        return GateOutcome(GateDecision.PASS, "pm", "Eligible for PM review.")
