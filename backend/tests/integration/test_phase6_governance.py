from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.market_data.models import OHLCVBar, Ticker
from apps.market_data.repositories import MarketDataRepository
from apps.orchestrator.models import AnalysisRun
from apps.orchestrator.services import AgentInputBuilder, PipelineService
from apps.portfolio.exceptions import ReviewConflictError
from apps.portfolio.models import PMRecommendation, RecommendationStatus
from apps.portfolio.services import PMReviewService
from apps.risk_compliance.models import PortfolioState, RiskLimit
from apps.users.models import User, UserRole

pytestmark = pytest.mark.django_db


@pytest.fixture
def ticker() -> Ticker:
    return Ticker.objects.create(symbol="PIT", exchange="US", name="Point In Time Inc.")


@pytest.fixture
def pm_user() -> User:
    return User.objects.create_user(
        username="governance-pm",
        email="governance-pm@example.com",
        password="test-password",
        role=UserRole.PORTFOLIO_MANAGER,
    )


def test_market_repository_excludes_late_arriving_and_future_data(ticker) -> None:
    cutoff = timezone.now() - timedelta(days=1)
    for suffix, timestamp, available_at, close in (
        ("known", cutoff - timedelta(hours=2), cutoff - timedelta(hours=1), 100),
        ("late", cutoff - timedelta(hours=3), cutoff + timedelta(hours=1), 200),
        ("future", cutoff + timedelta(hours=1), cutoff - timedelta(hours=1), 300),
    ):
        OHLCVBar.objects.create(
            ticker=ticker,
            timestamp=timestamp,
            open=close,
            high=close,
            low=close,
            close=close,
            adjusted_close=close,
            volume=1000,
            source_type="test",
            source_id=suffix,
            available_at=available_at,
            source_timestamp=timestamp,
            content_hash=suffix.ljust(64, "0"),
        )

    rows = MarketDataRepository().price_bars(ticker.symbol, as_of=cutoff)

    assert [row["source_id"] for row in rows] == ["known"]


def test_run_manifest_freezes_governance_and_configuration(ticker, pm_user) -> None:
    limit = RiskLimit.objects.create(
        metric="position_weight",
        maximum=0.1,
        severity="block",
    )
    run = PipelineService().create_run(
        ticker=ticker,
        initiated_by=pm_user,
        config={"horizon_days": 30},
    )

    limit.maximum = 0.2
    limit.save(update_fields=("maximum", "updated_at"))
    run.refresh_from_db()

    assert run.run_manifest["governance"]["risk_limits"]["position_weight"]["maximum"] == 0.1
    assert run.configuration_hash == run.run_manifest["configuration_hash"]
    assert len(run.manifest_hash) == 64


def test_external_risk_agent_payload_uses_aggregates_not_private_positions(
    ticker,
    pm_user,
) -> None:
    cutoff = timezone.now()
    PortfolioState.objects.create(
        portfolio_code="PRIVATE",
        name="Private Portfolio",
        owner=pm_user,
        as_of=cutoff,
        total_value=Decimal("2500000"),
        holdings=[{"symbol": "SECRET", "quantity": 999}],
        weights={"SECRET": 0.9},
        sector_exposures={"technology": 0.4},
        factor_exposures={"market": 0.7},
        liquidity_metrics={"days_to_liquidate": 2},
        risk_metrics={"var_95": 0.03},
        gross_leverage=1.1,
    )
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=pm_user,
        checkpoint_thread_id="phase6-private-data",
        data_cutoff_at=cutoff,
        analysis_config={"portfolio_code": "PRIVATE"},
    )

    payload = AgentInputBuilder().build(run, "risk")

    assert "holdings" not in payload["portfolio_state"]
    assert "weights" not in payload["portfolio_state"]
    assert payload["portfolio_state"]["risk_metrics"] == {"var_95": 0.03}


@patch("apps.portfolio.services.review_service.PMReviewService._resume")
def test_pm_review_is_versioned_idempotent_and_non_overridable(
    resume,
    ticker,
    pm_user,
    django_capture_on_commit_callbacks,
) -> None:
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=pm_user,
        checkpoint_thread_id="phase6-review",
        status="awaiting_pm_approval",
        current_stage="awaiting_pm_approval",
        analysis_config={"approval_gate": {"decision": "pass", "gate": "pm"}},
    )
    recommendation = PMRecommendation.objects.create(
        analysis_run=run,
        ticker=ticker,
        action="hold",
        conviction=65,
        summary="Reviewable draft.",
        rationale="Evidence.",
        time_horizon="medium_term",
        portfolio_fit="Within mandate.",
        capital_allocation_guidance="No allocation before review.",
    )
    service = PMReviewService()

    with django_capture_on_commit_callbacks(execute=True):
        first = service.submit(
            recommendation_id=recommendation.id,
            decision="approve",
            rationale="Approved after review.",
            reviewer=pm_user,
            expected_version=1,
            idempotency_key="phase6-review-1",
        )
    replay = service.submit(
        recommendation_id=recommendation.id,
        decision="approve",
        rationale="Approved after review.",
        reviewer=pm_user,
        expected_version=1,
        idempotency_key="phase6-review-1",
    )

    assert first.replayed is False
    assert replay.replayed is True
    assert first.request.lock_version == 2
    recommendation.refresh_from_db()
    assert recommendation.status == RecommendationStatus.APPROVED
    resume.assert_called_once()

    with pytest.raises(ReviewConflictError, match="already been reviewed"):
        service.submit(
            recommendation_id=recommendation.id,
            decision="reject",
            rationale="Conflicting action.",
            reviewer=pm_user,
            expected_version=2,
            idempotency_key="phase6-review-2",
        )
