from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agents.base.contracts import AgentOutputBase


class DebateArgument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thesis: str
    claims: list[str] = Field(min_length=1)
    challenged_assumptions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    invalidating_conditions: list[str] = Field(default_factory=list)


class ModeratorDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Literal["continue", "conclude"]
    rationale: str
    unresolved_questions: list[str] = Field(default_factory=list)


class BullBearDecisionMemo(AgentOutputBase):
    bull_case: str
    bear_case: str
    base_case: str
    weak_assumptions: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    invalidating_conditions: list[str] = Field(default_factory=list)
    material_unknowns: list[str] = Field(default_factory=list)
    premortem: list[str] = Field(default_factory=list)
