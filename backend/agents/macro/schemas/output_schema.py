from __future__ import annotations

from pydantic import Field

from agents.base.contracts import AgentOutputBase, AgentStance


class MacroAgentOutput(AgentOutputBase):
    regime: str
    regime_probability: float = Field(ge=0.0, le=1.0)
    transition_detected: bool
    equity_impact: AgentStance
    sector_impacts: dict[str, str] = Field(default_factory=dict)
    portfolio_risks: list[str] = Field(default_factory=list)
    monitoring_triggers: list[str] = Field(default_factory=list)
