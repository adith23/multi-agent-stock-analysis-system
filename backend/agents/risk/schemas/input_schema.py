from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from agents.base.contracts import AgentInputBase


class RiskAgentInput(AgentInputBase):
    proposed_trade: dict[str, Any] = Field(default_factory=dict)
    portfolio_state: dict[str, Any] = Field(default_factory=dict)
    var_inputs: dict[str, Any] | None = None
    stress_inputs: dict[str, Any] | None = None
    concentration_inputs: dict[str, Any] | None = None
    liquidity_inputs: dict[str, Any] | None = None
    limit_metrics: dict[str, float] = Field(default_factory=dict)
    limits: dict[str, dict[str, Any]] | None = None

    @model_validator(mode="after")
    def require_risk_context(self):
        if not any(
            (
                self.var_inputs,
                self.stress_inputs,
                self.concentration_inputs,
                self.liquidity_inputs,
                self.limit_metrics,
            )
        ):
            raise ValueError("at least one risk model or limit input is required")
        return self
