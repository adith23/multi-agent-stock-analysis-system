from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.core.domain.enums import ActionSignal, PipelineStatus
from apps.core.domain.exceptions import DomainValidationError
from apps.core.domain.value_objects import (
    ConvictionScore,
    ExitConditions,
    PositionSize,
    ReturnRange,
)


def test_action_signal_groups_are_disjoint() -> None:
    assert ActionSignal.BUY in ActionSignal.bullish_signals()
    assert ActionSignal.SELL in ActionSignal.bearish_signals()
    assert ActionSignal.bullish_signals().isdisjoint(ActionSignal.bearish_signals())
    assert "completed" in PipelineStatus.values()


def test_return_range_calculates_probability_weighted_return() -> None:
    return_range = ReturnRange(
        bear_case=Decimal("-10"),
        base_case=Decimal("10"),
        bull_case=Decimal("30"),
        bear_probability=Decimal("0.2"),
        base_probability=Decimal("0.5"),
        bull_probability=Decimal("0.3"),
    )

    assert return_range.expected_return() == Decimal("12")


@pytest.mark.parametrize(
    "probabilities",
    [
        (Decimal("0.2"), Decimal("0.2"), Decimal("0.2")),
        (Decimal("-0.1"), Decimal("0.6"), Decimal("0.5")),
    ],
)
def test_return_range_rejects_invalid_probabilities(probabilities) -> None:
    with pytest.raises(DomainValidationError):
        ReturnRange(
            bear_case=Decimal("-1"),
            base_case=Decimal("0"),
            bull_case=Decimal("1"),
            bear_probability=probabilities[0],
            base_probability=probabilities[1],
            bull_probability=probabilities[2],
        )


def test_return_range_rejects_unordered_scenarios() -> None:
    with pytest.raises(DomainValidationError, match="ordered"):
        ReturnRange(
            bear_case=Decimal("5"),
            base_case=Decimal("0"),
            bull_case=Decimal("1"),
            bear_probability=Decimal("0.2"),
            base_probability=Decimal("0.6"),
            bull_probability=Decimal("0.2"),
        )


def test_conviction_score_coerces_signal_and_validates_alignment() -> None:
    score = ConvictionScore(
        score=Decimal("84"),
        level=4,
        signal="buy",  # type: ignore[arg-type]
        aligned_agents=3,
        total_agents=4,
        consensus_degree=Decimal("0.75"),
    )

    assert score.signal is ActionSignal.BUY

    with pytest.raises(DomainValidationError):
        ConvictionScore(
            score=Decimal("101"),
            level=5,
            signal=ActionSignal.BUY,
            aligned_agents=4,
            total_agents=4,
            consensus_degree=Decimal("1"),
        )


def test_position_size_and_exit_conditions_enforce_invariants() -> None:
    size = PositionSize(
        portfolio_weight_pct=Decimal("3.5"),
        num_shares=10,
        dollar_amount=Decimal("500"),
        methodology="vol_target",
        entry_tranches=2,
        risk_budget_contribution=Decimal("0.5"),
    )
    assert size.entry_tranches == 2

    conditions = ExitConditions(
        stop_loss_price=Decimal("90"),
        stop_loss_pct=Decimal("10"),
        profit_target_price=Decimal("120"),
        profit_target_pct=Decimal("20"),
        trailing_stop_pct=Decimal("5"),
        thesis_invalidation_triggers=("guidance withdrawal",),
        time_based_review_date=datetime(2026, 8, 1, tzinfo=UTC),
    )
    assert conditions.stop_loss_price == Decimal("90")

    with pytest.raises(DomainValidationError, match="timezone-aware"):
        ExitConditions(
            stop_loss_price=Decimal("90"),
            stop_loss_pct=Decimal("10"),
            profit_target_price=Decimal("120"),
            profit_target_pct=Decimal("20"),
            trailing_stop_pct=None,
            thesis_invalidation_triggers=("trigger",),
            time_based_review_date=datetime(2026, 8, 1),
        )
