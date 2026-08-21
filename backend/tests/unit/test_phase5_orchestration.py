from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.core.domain.enums import PipelineStatus, RiskDecision
from apps.market_data.models import OHLCVBar, Ticker
from apps.orchestrator.models import AnalysisRun
from apps.orchestrator.services import ApprovalChain, GateDecision, PipelineStepService
from apps.portfolio.models import (
    ExitPackageStatus,
    ExitStrategyPackage,
    PerformanceAttributionRecord,
    PMRecommendation,
)
from apps.portfolio.services import (
    CatalystMonitorService,
    ExitMonitorService,
    PerformanceService,
    PortfolioService,
)
from apps.research.models import CatalystRecord
from apps.risk_compliance.services import RiskService

pytestmark = pytest.mark.django_db


@pytest.fixture
def ticker() -> Ticker:
    return Ticker.objects.create(symbol="ACME", exchange="US", name="Acme Corp")


@pytest.fixture
def analysis_run(ticker: Ticker, user) -> AnalysisRun:
    return AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id="analysis-phase5-test",
    )


def test_analysis_run_enforces_ordered_state_transitions(analysis_run: AnalysisRun) -> None:
    analysis_run.transition_to(PipelineStatus.INGESTING)
    analysis_run.transition_to(PipelineStatus.EXTRACTING_SIGNALS)

    assert analysis_run.status == PipelineStatus.EXTRACTING_SIGNALS
    assert analysis_run.started_at is not None

    with pytest.raises(ValueError, match="invalid pipeline transition"):
        analysis_run.transition_to(PipelineStatus.PM_SYNTHESIS)


def test_pipeline_step_tracker_persists_each_retry_attempt(
    analysis_run: AnalysisRun,
) -> None:
    tracker = PipelineStepService()
    with (
        pytest.raises(RuntimeError, match="temporary"),
        tracker.track(analysis_run, name="agent_macro", sequence=3, attempt=1),
    ):
        raise RuntimeError("temporary")

    with tracker.track(
        analysis_run,
        name="agent_macro",
        sequence=3,
        attempt=2,
    ) as output:
        output["confidence"] = 0.8

    attempts = list(analysis_run.steps.order_by("attempt"))
    assert [item.status for item in attempts] == ["failed", "completed"]
    assert attempts[1].output_snapshot == {"confidence": 0.8}


def test_risk_block_is_binding_in_approval_chain(analysis_run: AnalysisRun) -> None:
    result = RiskService().validate(
        analysis_run,
        metrics={"position_weight": 0.25},
        agent_output={"disposition": "pass", "rationale": "Agent found no extra issue."},
    )

    assert result.decision == RiskDecision.BLOCK
    assert result.rule_version

    # Compliance is required by the next gate but must not be reached after a risk block.
    outcome = ApprovalChain().evaluate(analysis_run)
    assert outcome.decision is GateDecision.BLOCK
    assert outcome.gate == "risk"


def test_binding_gate_generates_zero_sizing_and_no_trade_portfolio(
    analysis_run: AnalysisRun,
) -> None:
    service = PortfolioService()
    sizing = service.create_no_position_sizing(
        analysis_run,
        reason="Restricted security.",
        inputs={
            "portfolio_value": 100_000,
            "price": 100,
        },
    )
    construction = service.hold_current_allocations(
        analysis_run,
        inputs={"current_weights": {"ACME": 0.0}},
        reason="Restricted security.",
    )

    assert sizing.dollar_amount == Decimal("0")
    assert sizing.num_shares == 0
    assert construction.target_allocations == {"ACME": 0.0}
    assert construction.rebalance_required is False


def test_performance_tracking_is_point_in_time_and_idempotent(
    analysis_run: AnalysisRun,
) -> None:
    now = timezone.now()
    reviewed_at = now - timedelta(days=5)
    recommendation = PMRecommendation.objects.create(
        analysis_run=analysis_run,
        ticker=analysis_run.ticker,
        action="buy",
        conviction=80,
        status="approved",
        summary="Approved idea",
        rationale="Evidence",
        time_horizon="medium_term",
        portfolio_fit="Within mandate",
        capital_allocation_guidance="Scale in",
        reviewed_at=reviewed_at,
    )
    for index, close in enumerate((100, 110, 108)):
        timestamp = reviewed_at + timedelta(days=index)
        OHLCVBar.objects.create(
            ticker=analysis_run.ticker,
            timestamp=timestamp,
            open=close,
            high=close,
            low=close,
            close=close,
            adjusted_close=close,
            volume=1_000,
            source_type="test",
            source_timestamp=timestamp,
            content_hash=f"{index:064d}",
        )

    service = PerformanceService(periods={"1d": 1})
    first = service.track_due(as_of=now)
    second = service.track_due(as_of=now)

    assert first == {"checked": 1, "created": 1}
    assert second == {"checked": 1, "created": 0}
    record = PerformanceAttributionRecord.objects.get(recommendation=recommendation)
    assert record.realized_return == pytest.approx(0.1)
    assert record.hit is True
    assert PerformanceService.summary()["hit_rate"] == 1.0


def test_scheduled_monitors_trigger_exits_and_delayed_critical_catalysts(
    analysis_run: AnalysisRun,
) -> None:
    now = timezone.now()
    ExitStrategyPackage.objects.create(
        analysis_run=analysis_run,
        status=ExitPackageStatus.ACTIVE,
        entry_price=100,
        stop_loss_price=90,
        stop_loss_pct=0.10,
        profit_targets=[{"price": 120}],
        time_based_review_date=now + timedelta(days=30),
    )
    OHLCVBar.objects.create(
        ticker=analysis_run.ticker,
        timestamp=now,
        open=85,
        high=85,
        low=85,
        close=85,
        volume=1_000,
        source_type="test",
        source_timestamp=now,
        content_hash="e" * 64,
    )
    catalyst = CatalystRecord.objects.create(
        analysis_run_id=analysis_run.id,
        run=analysis_run,
        ticker=analysis_run.ticker,
        title="Regulatory decision",
        description="Expected decision date",
        catalyst_type="regulatory",
        expected_at=now - timedelta(days=1),
        is_thesis_critical=True,
    )

    exit_result = ExitMonitorService().monitor()
    catalyst_result = CatalystMonitorService().monitor()

    analysis_run.exit_package.refresh_from_db()
    catalyst.refresh_from_db()
    assert exit_result == {"checked": 1, "triggered": 1}
    assert analysis_run.exit_package.trigger_type == "stop_loss"
    assert catalyst_result == {"checked": 1, "delayed": 1}
    assert catalyst.outcome_status == "delayed"
    assert catalyst.alert_sent is True
