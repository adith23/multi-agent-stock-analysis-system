"""Stable domain taxonomies used in contracts, persistence, and APIs."""

from __future__ import annotations

from enum import StrEnum


class DomainEnum(StrEnum):
    """String enum with helpers suitable for Django/Pydantic choices."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(member.value for member in cls)

    @classmethod
    def choices(cls) -> tuple[tuple[str, str], ...]:
        return tuple((member.value, member.name.replace("_", " ").title()) for member in cls)


class ActionSignal(DomainEnum):
    """FR-061/FR-082 discrete action signal taxonomy."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    ACCUMULATE = "accumulate"
    HOLD = "hold"
    REDUCE = "reduce"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    NOT_BUY = "not_buy"
    NOT_SELL = "not_sell"

    @classmethod
    def bullish_signals(cls) -> frozenset[ActionSignal]:
        return frozenset({cls.STRONG_BUY, cls.BUY, cls.ACCUMULATE})

    @classmethod
    def bearish_signals(cls) -> frozenset[ActionSignal]:
        return frozenset({cls.STRONG_SELL, cls.SELL, cls.REDUCE})


class TimeHorizon(DomainEnum):
    TACTICAL = "tactical"
    MEDIUM_TERM = "medium_term"
    STRATEGIC = "strategic"


class RegimeState(DomainEnum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    TIGHTENING = "tightening"
    EASING = "easing"
    INFLATIONARY = "inflationary"
    RECESSIONARY = "recessionary"
    LIQUIDITY_STRESSED = "liquidity_stressed"


class AgentStance(DomainEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PipelineStatus(DomainEnum):
    PENDING = "pending"
    INGESTING = "ingesting"
    EXTRACTING_SIGNALS = "extracting_signals"
    RUNNING_SPECIALISTS = "running_specialists"
    PEER_ANALYSIS = "peer_analysis"
    ADVERSARIAL_REVIEW = "adversarial_review"
    CONVICTION_SCORING = "conviction_scoring"
    RISK_VALIDATION = "risk_validation"
    COMPLIANCE_CHECK = "compliance_check"
    POSITION_SIZING = "position_sizing"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    PM_SYNTHESIS = "pm_synthesis"
    AWAITING_PM_APPROVAL = "awaiting_pm_approval"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskDecision(DomainEnum):
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    REDUCE_SIZE = "reduce_size"
    HEDGE_REQUIRED = "hedge_required"
    BLOCK = "block"
    ESCALATE = "escalate"


class ComplianceDecision(DomainEnum):
    APPROVED = "approved"
    RESTRICTED = "restricted"
    REQUIRES_APPROVAL = "requires_approval"
    VIOLATED = "violated"
    ESCALATED = "escalated"
