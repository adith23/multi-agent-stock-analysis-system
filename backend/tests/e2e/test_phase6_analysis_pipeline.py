from __future__ import annotations

from contextlib import nullcontext
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core.domain.enums import PipelineStatus
from apps.market_data.models import OHLCVBar, Ticker
from apps.orchestrator.models import AnalysisRun
from apps.portfolio.models import PMReviewRequest

pytestmark = pytest.mark.django_db(transaction=True)

SPECIALIST_OUTPUTS = {
    "macro": {
        "summary": "Macro conditions are balanced.",
        "rationale": "Current regime evidence is neutral.",
        "confidence": 0.7,
        "equity_impact": "neutral",
    },
    "fundamental": {
        "summary": "Fundamentals support a measured stance.",
        "rationale": "Balance sheet evidence is adequate.",
        "confidence": 0.75,
        "stance": "bullish",
        "thesis": "Fundamentals are constructive.",
    },
    "technical": {
        "summary": "Price trend is constructive.",
        "rationale": "Signals agree on an upward trend.",
        "confidence": 0.8,
        "stance": "bullish",
    },
    "sentiment": {
        "summary": "Narrative is balanced.",
        "rationale": "No extreme attention signal is present.",
        "confidence": 0.65,
        "stance": "neutral",
    },
    "risk": {
        "summary": "Risk checks passed.",
        "rationale": "The proposal remains within limits.",
        "confidence": 0.9,
        "disposition": "pass",
        "approved": True,
        "risk_budget_impact": "within budget",
    },
}


class StubSpecialistGraph:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

    def invoke(self, *args, **kwargs):
        return {"agent_output": SPECIALIST_OUTPUTS[self.agent_id]}


class StubAdversarialGraph:
    def invoke(self, *args, **kwargs):
        return {
            "debate_round": 1,
            "agent_output": {
                "summary": "The debate is balanced.",
                "rationale": "Both upside and downside evidence were challenged.",
                "confidence": 0.72,
                "bull_case": "Constructive operating evidence.",
                "bear_case": "Valuation and macro uncertainty.",
                "base_case": "Measured upside with monitored risks.",
            },
        }


class StubPMGraph:
    def invoke(self, *args, **kwargs):
        return {
            "draft_recommendation": {
                "action": "hold",
                "conviction": 70,
                "summary": "Hold pending human approval.",
                "rationale": "The evidence is constructive but not decisive.",
                "time_horizon": "medium_term",
                "portfolio_fit": "Within the configured mandate.",
                "capital_allocation_guidance": "Maintain current exposure.",
            }
        }


def test_api_to_eager_celery_pipeline_persists_reviewable_recommendation(
    authenticated_client,
    ticker_and_bars,
    monkeypatch,
) -> None:
    ticker = ticker_and_bars
    monkeypatch.setattr(
        "apps.orchestrator.tasks.get_checkpointer",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        "apps.orchestrator.tasks.AgentRegistry.create",
        lambda agent_id, **kwargs: StubSpecialistGraph(agent_id),
    )
    monkeypatch.setattr(
        "apps.orchestrator.tasks.build_adversarial_agent_graph",
        lambda **kwargs: StubAdversarialGraph(),
    )
    monkeypatch.setattr(
        "apps.orchestrator.tasks.build_pm_agent_graph",
        lambda **kwargs: StubPMGraph(),
    )

    response = authenticated_client.post(
        reverse("api-v1:analysis-list"),
        {
            "symbol": ticker.symbol,
            "exchange": ticker.exchange,
            "config": {"portfolio_value": 100000},
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="phase6-e2e-analysis-1",
    )

    assert response.status_code == 202, AnalysisRun.objects.get().error_message
    run = AnalysisRun.objects.get(pk=response.data["id"])
    assert run.status == PipelineStatus.AWAITING_PM_APPROVAL
    assert run.specialist_reports.count() == 4
    assert run.steps.filter(status="failed").count() == 0
    assert run.steps.filter(status="completed").count() == 17
    assert run.recommendation.status == "pending_review"
    assert PMReviewRequest.objects.filter(recommendation=run.recommendation).exists()
    assert run.run_manifest["point_in_time_policy"]["future_observations_permitted"] is False

    detail = authenticated_client.get(reverse("api-v1:analysis-detail", kwargs={"run_id": run.id}))
    recommendation = authenticated_client.get(
        reverse("api-v1:analysis-recommendation", kwargs={"run_id": run.id})
    )
    assert detail.status_code == 200
    # A research analyst can track the run but cannot access the sensitive PM draft.
    assert recommendation.status_code == 403


@pytest.fixture
def ticker_and_bars() -> Ticker:
    ticker = Ticker.objects.create(symbol="E2E", exchange="US", name="E2E Corp")
    now = timezone.now()
    for index in range(260):
        timestamp = now - timedelta(days=260 - index)
        close = 100 + index * 0.1
        OHLCVBar.objects.create(
            ticker=ticker,
            timestamp=timestamp,
            open=close,
            high=close + 1,
            low=close - 1,
            close=close,
            adjusted_close=close,
            volume=100000 + index,
            source_type="e2e",
            source_id=f"bar-{index}",
            source_timestamp=timestamp,
            available_at=timestamp,
            content_hash=f"{index:064x}",
        )
    return ticker
