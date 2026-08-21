from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from agents.base.contracts import AgentOutputBase
from apps.core.domain.enums import ActionSignal


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"


class HumanReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: ReviewDecision
    rationale: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)


class PMRecommendation(AgentOutputBase):
    action: ActionSignal
    conviction: float = Field(ge=0.0, le=100.0)
    decision_status: str = "pending_review"
    expected_return: dict[str, float] = Field(default_factory=dict)
    position_size: dict[str, object] = Field(default_factory=dict)
    entry_plan: list[str] = Field(default_factory=list)
    exit_conditions: dict[str, object] = Field(default_factory=dict)
    time_horizon: str
    catalysts: list[dict[str, object]] = Field(default_factory=list)
    portfolio_fit: str
    capital_allocation_guidance: str
    conditions_precedent: list[str] = Field(default_factory=list)
    human_review: dict[str, str] | None = None
