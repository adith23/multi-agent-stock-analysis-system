from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from agents.base.contracts import AgentOutputBase


class RiskDisposition(StrEnum):
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    REDUCE_SIZE = "reduce_size"
    ESCALATE = "escalate"
    BLOCK = "block"


class RiskAgentOutput(AgentOutputBase):
    disposition: RiskDisposition
    approved: bool
    risk_budget_impact: str
    concentration_risks: list[str] = Field(default_factory=list)
    liquidity_risks: list[str] = Field(default_factory=list)
    tail_risks: list[str] = Field(default_factory=list)
    limit_breaches: list[str] = Field(default_factory=list)
    mitigations: list[str] = Field(default_factory=list)
    hedge_suggestions: list[str] = Field(default_factory=list)
