"""Immutable value objects that enforce financial-domain invariants."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .enums import ActionSignal
from .exceptions import DomainValidationError

ZERO = Decimal("0")
ONE = Decimal("1")
ONE_HUNDRED = Decimal("100")


def _between(name: str, value: Decimal, minimum: Decimal, maximum: Decimal) -> None:
    if not minimum <= value <= maximum:
        raise DomainValidationError(f"{name} must be between {minimum} and {maximum}")


@dataclass(frozen=True, slots=True)
class ReturnRange:
    """FR-063 expected return scenarios and their probabilities."""

    bear_case: Decimal
    base_case: Decimal
    bull_case: Decimal
    bear_probability: Decimal
    base_probability: Decimal
    bull_probability: Decimal

    def __post_init__(self) -> None:
        probabilities = (
            self.bear_probability,
            self.base_probability,
            self.bull_probability,
        )
        for index, probability in enumerate(probabilities):
            _between(f"probability[{index}]", probability, ZERO, ONE)
        if sum(probabilities, ZERO) != ONE:
            raise DomainValidationError("scenario probabilities must sum to 1")
        if not self.bear_case <= self.base_case <= self.bull_case:
            raise DomainValidationError("return scenarios must be ordered bear <= base <= bull")

    def expected_return(self) -> Decimal:
        return (
            self.bear_case * self.bear_probability
            + self.base_case * self.base_probability
            + self.bull_case * self.bull_probability
        )


@dataclass(frozen=True, slots=True)
class ConvictionScore:
    """FR-061 structured conviction with signal-agreement evidence."""

    score: Decimal
    level: int
    signal: ActionSignal
    aligned_agents: int
    total_agents: int
    consensus_degree: Decimal

    def __post_init__(self) -> None:
        _between("score", self.score, ZERO, ONE_HUNDRED)
        _between("consensus_degree", self.consensus_degree, ZERO, ONE)
        if not 1 <= self.level <= 5:
            raise DomainValidationError("level must be between 1 and 5")
        if self.total_agents <= 0:
            raise DomainValidationError("total_agents must be positive")
        if not 0 <= self.aligned_agents <= self.total_agents:
            raise DomainValidationError("aligned_agents must be between 0 and total_agents")
        if not isinstance(self.signal, ActionSignal):
            object.__setattr__(self, "signal", ActionSignal(self.signal))


@dataclass(frozen=True, slots=True)
class PositionSize:
    """FR-069 position sizing output."""

    portfolio_weight_pct: Decimal
    num_shares: int
    dollar_amount: Decimal
    methodology: str
    entry_tranches: int
    risk_budget_contribution: Decimal

    def __post_init__(self) -> None:
        _between("portfolio_weight_pct", self.portfolio_weight_pct, ZERO, ONE_HUNDRED)
        if self.num_shares < 0 or self.dollar_amount < ZERO:
            raise DomainValidationError("position quantities cannot be negative")
        if not self.methodology.strip():
            raise DomainValidationError("methodology is required")
        if self.entry_tranches < 1:
            raise DomainValidationError("entry_tranches must be at least 1")
        if self.risk_budget_contribution < ZERO:
            raise DomainValidationError("risk budget contribution cannot be negative")


@dataclass(frozen=True, slots=True)
class ExitConditions:
    """FR-072 immutable exit-strategy package."""

    stop_loss_price: Decimal
    stop_loss_pct: Decimal
    profit_target_price: Decimal
    profit_target_pct: Decimal
    trailing_stop_pct: Decimal | None
    thesis_invalidation_triggers: tuple[str, ...]
    time_based_review_date: datetime

    def __post_init__(self) -> None:
        if self.stop_loss_price < ZERO or self.profit_target_price < ZERO:
            raise DomainValidationError("exit prices cannot be negative")
        if self.stop_loss_pct < ZERO or self.profit_target_pct < ZERO:
            raise DomainValidationError("exit percentages cannot be negative")
        if self.trailing_stop_pct is not None:
            _between("trailing_stop_pct", self.trailing_stop_pct, ZERO, ONE_HUNDRED)
        if not self.thesis_invalidation_triggers:
            raise DomainValidationError("at least one thesis invalidation trigger is required")
        if self.time_based_review_date.tzinfo is None:
            raise DomainValidationError("time_based_review_date must be timezone-aware")
