from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core.domain.enums import PipelineStatus
from apps.market_data.models import Ticker
from apps.orchestrator.models import AnalysisRun
from apps.portfolio.models import PerformanceAttributionRecord, PMRecommendation
from apps.research.models import CatalystRecord
from apps.risk_compliance.models import PortfolioState
from apps.users.models import User, UserRole

pytestmark = pytest.mark.django_db


@pytest.fixture
def ticker() -> Ticker:
    return Ticker.objects.create(symbol="ACME", exchange="US", name="Acme Corp")


@pytest.fixture
def pm_user() -> User:
    return User.objects.create_user(
        username="phase6-pm",
        email="phase6-pm@example.com",
        password="test-password",
        role=UserRole.PORTFOLIO_MANAGER,
    )


@pytest.fixture
def pm_client(api_client, pm_user):
    api_client.force_authenticate(pm_user)
    return api_client


def _run(ticker: Ticker, user: User, suffix: str, **kwargs) -> AnalysisRun:
    return AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id=f"phase6-{suffix}",
        **kwargs,
    )


@patch("apps.orchestrator.services.pipeline_service.PipelineService.dispatch")
def test_analysis_creation_is_idempotent_and_rejects_key_reuse(
    dispatch,
    authenticated_client,
    ticker,
) -> None:
    dispatch.return_value = "task-1"
    url = reverse("api-v1:analysis-list")
    request = {"symbol": "ACME", "exchange": "US", "config": {}}

    first = authenticated_client.post(
        url,
        request,
        format="json",
        HTTP_IDEMPOTENCY_KEY="analysis-idempotency-1",
    )
    replay = authenticated_client.post(
        url,
        request,
        format="json",
        HTTP_IDEMPOTENCY_KEY="analysis-idempotency-1",
    )
    conflict = authenticated_client.post(
        url,
        {**request, "config": {"horizon_days": 20}},
        format="json",
        HTTP_IDEMPOTENCY_KEY="analysis-idempotency-1",
    )

    assert first.status_code == 202
    assert replay.status_code == 200
    assert replay.data["id"] == first.data["id"]
    assert conflict.status_code == 409
    assert AnalysisRun.objects.count() == 1
    dispatch.assert_called_once()


def test_analysis_list_supports_filter_search_order_and_pagination(
    authenticated_client,
    ticker,
    user,
) -> None:
    _run(ticker, user, "older", status=PipelineStatus.PENDING)
    _run(ticker, user, "newer", status=PipelineStatus.COMPLETED)

    response = authenticated_client.get(
        reverse("api-v1:analysis-list"),
        {
            "symbol": "acme",
            "status": PipelineStatus.COMPLETED,
            "search": "Acme",
            "ordering": "-created_at",
            "page_size": 1,
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["status"] == PipelineStatus.COMPLETED


def test_analysis_input_rejects_secrets_unsafe_keys_and_multi_security_scope(
    authenticated_client,
    ticker,
) -> None:
    url = reverse("api-v1:analysis-list")
    secret = authenticated_client.post(
        url,
        {
            "symbol": ticker.symbol,
            "config": {"risk_metrics": {"api_key": "must-not-enter-run-state"}},
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="analysis-secret-1",
    )
    control_char = authenticated_client.post(
        url,
        {"symbol": ticker.symbol},
        format="json",
        HTTP_IDEMPOTENCY_KEY="unsafe key",
    )
    multi = authenticated_client.post(
        url,
        {"symbol": ticker.symbol, "scope": "watchlist"},
        format="json",
        HTTP_IDEMPOTENCY_KEY="analysis-watchlist-1",
    )

    assert secret.status_code == 400
    assert "credentials or secrets" in str(secret.data)
    assert control_char.status_code == 400
    assert multi.status_code == 400


def test_sensitive_portfolio_routes_are_rbac_protected_and_return_latest_snapshot(
    authenticated_client,
    pm_client,
    pm_user,
    user,
) -> None:
    now = timezone.now()
    PortfolioState.objects.create(
        portfolio_code="CORE",
        name="Core Portfolio",
        owner=pm_user,
        as_of=now,
        total_value=Decimal("1000000"),
        holdings=[{"symbol": "ACME", "quantity": 100}],
        weights={"ACME": 0.1},
        sector_exposures={"technology": 0.1},
        factor_exposures={"market": 0.8},
        liquidity_metrics={"days_to_liquidate": 1},
        risk_metrics={"var_95": 0.02},
        gross_leverage=1.0,
    )

    authenticated_client.force_authenticate(user)
    forbidden = authenticated_client.get(reverse("api-v1:portfolio"))
    pm_client.force_authenticate(pm_user)
    portfolio = pm_client.get(
        reverse("api-v1:portfolio"),
        {"portfolio_code": "CORE"},
    )
    risk = pm_client.get(reverse("api-v1:portfolio-risk"))

    assert forbidden.status_code == 403
    assert portfolio.status_code == 200
    assert portfolio.data["portfolio_code"] == "CORE"
    assert risk.data["risk_metrics"] == {"var_95": 0.02}


def test_scenario_endpoint_validates_bounds_and_persists_auditable_result(
    pm_client,
) -> None:
    url = reverse("api-v1:scenario-create")
    payload = {
        "name": "rates-up",
        "positions": {"ACME": 1000},
        "factor_exposures": {"ACME": {"rates": -0.5}},
        "factor_shocks": {"rates": 0.1},
        "asset_shocks": {"ACME": -0.05},
    }

    created = pm_client.post(url, payload, format="json")
    invalid = pm_client.post(
        url,
        {**payload, "factor_shocks": {"rates": 6.0}},
        format="json",
    )

    assert created.status_code == 201
    assert created.data["results"]["portfolio_pnl"] == -100.0
    assert invalid.status_code == 400


def test_catalyst_performance_and_alert_read_models(
    authenticated_client,
    pm_client,
    ticker,
    pm_user,
) -> None:
    now = timezone.now()
    run = _run(ticker, pm_user, "read-models")
    recommendation = PMRecommendation.objects.create(
        analysis_run=run,
        ticker=ticker,
        action="buy",
        conviction=75,
        summary="Approved thesis.",
        rationale="Evidence.",
        time_horizon="medium_term",
        portfolio_fit="Within mandate.",
        capital_allocation_guidance="Scale in.",
    )
    PerformanceAttributionRecord.objects.create(
        recommendation=recommendation,
        measurement_period="1d",
        period_start=now - timedelta(days=1),
        period_end=now,
        entry_price=100,
        exit_price=105,
        realized_return=0.05,
        benchmark_return=0.01,
        excess_return=0.04,
        hit=True,
    )
    CatalystRecord.objects.create(
        analysis_run_id=run.id,
        run=run,
        ticker=ticker,
        title="Regulatory decision",
        description="Decision was delayed.",
        catalyst_type="regulatory",
        expected_at=now - timedelta(days=1),
        is_thesis_critical=True,
        outcome_status="delayed",
        alert_sent=True,
        last_checked_at=now,
    )

    catalysts = authenticated_client.get(
        reverse("api-v1:catalyst-list"),
        {"search": "Regulatory", "is_thesis_critical": "true"},
    )
    performance = pm_client.get(
        reverse("api-v1:performance"),
        {"symbol": "ACME", "measurement_period": "1d"},
    )
    alerts = pm_client.get(reverse("api-v1:alert-list"), {"severity": "critical"})

    assert catalysts.status_code == 200
    assert catalysts.data["count"] == 1
    assert performance.status_code == 200
    assert performance.data["results"]["summary"]["hit_rate"] == 1.0
    assert alerts.status_code == 200
    assert alerts.data["count"] == 1
    assert alerts.data["results"][0]["type"] == "catalyst_delayed"
