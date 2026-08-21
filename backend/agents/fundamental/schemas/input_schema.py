from __future__ import annotations

from typing import Any

from pydantic import Field

from agents.base.contracts import AgentInputBase


class FundamentalAgentInput(AgentInputBase):
    financials: dict[str, Any] = Field(default_factory=dict)
    company_profile: dict[str, Any] = Field(default_factory=dict)
    dcf_inputs: dict[str, Any] | None = None
    multiples_inputs: dict[str, Any] | None = None
    earnings_quality_inputs: dict[str, Any] | None = None
    peer_inputs: dict[str, Any] | None = None
    macro_context: dict[str, Any] = Field(default_factory=dict)
