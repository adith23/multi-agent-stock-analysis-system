from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.core.domain.enums import PipelineStatus
from apps.market_data.models import Ticker
from apps.orchestrator.models import AnalysisRun
from apps.portfolio.models import PMRecommendation, RecommendationStatus
from apps.users.models import User, UserRole

pytestmark = pytest.mark.django_db


@pytest.fixture
def ticker() -> Ticker:
    return Ticker.objects.create(symbol="ACME", exchange="US", name="Acme Corp")


@pytest.fixture
def pm_user() -> User:
    return User.objects.create_user(
        username="pm",
        email="pm@example.com",
        password="test-password",
        role=UserRole.PORTFOLIO_MANAGER,
    )


def _awaiting_run(ticker: Ticker, pm_user: User, *, gate: str = "pass") -> AnalysisRun:
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=pm_user,
        checkpoint_thread_id=f"analysis-api-{gate}",
        status=PipelineStatus.AWAITING_PM_APPROVAL,
        current_stage=PipelineStatus.AWAITING_PM_APPROVAL,
        analysis_config={
            "approval_gate": {
                "decision": gate,
                "gate": "pm" if gate == "pass" else "risk",
                "rationale": "Eligible." if gate == "pass" else "Blocked.",
            }
        },
    )
    PMRecommendation.objects.create(
        analysis_run=run,
        ticker=ticker,
        action="hold",
        conviction=65,
        summary="Draft",
        rationale="Evidence-based draft.",
        time_horizon="medium_term",
        portfolio_fit="Fits mandate.",
        capital_allocation_guidance="No allocation before review.",
    )
    return run


@patch("apps.orchestrator.services.pipeline_service.PipelineService.dispatch")
def test_analysis_api_creates_and_dispatches_run(
    dispatch,
    authenticated_client,
    ticker: Ticker,
) -> None:
    dispatch.return_value = "celery-task-1"

    response = authenticated_client.post(
        reverse("api-v1:analysis-list"),
        {"symbol": "acme", "exchange": "us", "config": {}},
        format="json",
        HTTP_IDEMPOTENCY_KEY="analysis-create-1",
    )

    assert response.status_code == 202
    assert response.data["symbol"] == "ACME"
    run = AnalysisRun.objects.get(pk=response.data["id"])
    assert run.initiated_by.username == "analyst"
    dispatch.assert_called_once_with(run)


@patch("apps.portfolio.services.review_service.PMReviewService._resume")
def test_pm_can_approve_eligible_recommendation(
    resume,
    api_client,
    ticker: Ticker,
    pm_user: User,
    django_capture_on_commit_callbacks,
) -> None:
    run = _awaiting_run(ticker, pm_user)
    api_client.force_authenticate(pm_user)

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(
            reverse("api-v1:analysis-approve", kwargs={"run_id": run.id}),
            {"rationale": "Approved within mandate.", "expected_version": 1},
            format="json",
            HTTP_IDEMPOTENCY_KEY="pm-review-approve-1",
        )

    assert response.status_code == 202
    run.recommendation.refresh_from_db()
    assert run.recommendation.status == RecommendationStatus.APPROVED
    resume.assert_called_once_with(
        run_id=str(run.id),
        decision="approve",
        rationale="Approved within mandate.",
        reviewer_id=str(pm_user.id),
    )


@patch("apps.portfolio.services.review_service.PMReviewService._resume")
def test_pm_cannot_approve_binding_risk_block(
    resume,
    api_client,
    ticker: Ticker,
    pm_user: User,
) -> None:
    run = _awaiting_run(ticker, pm_user, gate="block")
    api_client.force_authenticate(pm_user)

    response = api_client.post(
        reverse("api-v1:analysis-approve", kwargs={"run_id": run.id}),
        {"rationale": "Attempted override.", "expected_version": 1},
        format="json",
        HTTP_IDEMPOTENCY_KEY="pm-review-blocked-1",
    )

    assert response.status_code == 400
    run.recommendation.refresh_from_db()
    assert run.recommendation.status == RecommendationStatus.PENDING_REVIEW
    resume.assert_not_called()


def test_research_analyst_cannot_read_sensitive_risk_result(
    authenticated_client,
    ticker: Ticker,
    user: User,
) -> None:
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id="analysis-sensitive",
    )

    response = authenticated_client.get(reverse("api-v1:analysis-risk", kwargs={"run_id": run.id}))

    assert response.status_code == 403
