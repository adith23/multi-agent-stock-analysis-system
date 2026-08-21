from __future__ import annotations

from typing import Any, NotRequired

from agents.base.state import AgentState


class FundamentalAgentState(AgentState):
    financials: NotRequired[dict[str, Any]]
    company_profile: NotRequired[dict[str, Any]]
    valuation: NotRequired[dict[str, Any]]
    earnings_quality: NotRequired[dict[str, Any]]
    peer_comparison: NotRequired[dict[str, Any]]
    prior_context: NotRequired[list[dict[str, Any]]]
