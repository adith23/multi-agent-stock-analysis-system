from __future__ import annotations

from pydantic import Field

from agents.base.contracts import AgentOutputBase, AgentStance


class FundamentalAgentOutput(AgentOutputBase):
    stance: AgentStance
    thesis: str
    bull_drivers: list[str] = Field(default_factory=list)
    bear_drivers: list[str] = Field(default_factory=list)
    fair_value_low: float | None = None
    fair_value_base: float | None = None
    fair_value_high: float | None = None
    quality_assessment: str
    moat_assessment: str
    management_assessment: str
    key_falsifiers: list[str] = Field(default_factory=list)
