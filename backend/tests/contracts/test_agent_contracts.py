from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import BaseModel, ValidationError

from agents.adversarial.schemas import AdversarialAgentInput, BullBearDecisionMemo
from agents.fundamental.schemas import FundamentalAgentInput, FundamentalAgentOutput
from agents.macro.schemas import MacroAgentInput, MacroAgentOutput
from agents.pm.schemas import PMAgentInput, PMRecommendation
from agents.risk.schemas import RiskAgentInput, RiskAgentOutput
from agents.sentiment.schemas import SentimentAgentInput, SentimentAgentOutput
from agents.technical.schemas import TechnicalAgentInput, TechnicalAgentOutput

BASE_INPUT = {
    "analysis_run_id": "00000000-0000-0000-0000-000000000001",
    "ticker": "TEST",
}
BASE_OUTPUT = {
    "summary": "Evidence-supported result.",
    "rationale": "Deterministic evidence supports the result.",
    "confidence": 0.75,
}

CONTRACT_CASES: tuple[tuple[type[BaseModel], dict], ...] = (
    (MacroAgentInput, {**BASE_INPUT}),
    (
        MacroAgentOutput,
        {
            **BASE_OUTPUT,
            "regime": "regime_1",
            "regime_probability": 0.8,
            "transition_detected": False,
            "equity_impact": "neutral",
        },
    ),
    (FundamentalAgentInput, {**BASE_INPUT}),
    (
        FundamentalAgentOutput,
        {
            **BASE_OUTPUT,
            "stance": "neutral",
            "thesis": "The evidence is balanced.",
            "quality_assessment": "adequate",
            "moat_assessment": "uncertain",
            "management_assessment": "credible",
        },
    ),
    (
        TechnicalAgentInput,
        {**BASE_INPUT, "ohlcv": [{} for _ in range(35)]},
    ),
    (
        TechnicalAgentOutput,
        {
            **BASE_OUTPUT,
            "stance": "neutral",
            "trend_state": "range",
            "timing_cue": "wait",
            "momentum_state": "balanced",
            "relative_strength_view": "in-line",
        },
    ),
    (SentimentAgentInput, {**BASE_INPUT}),
    (
        SentimentAgentOutput,
        {
            **BASE_OUTPUT,
            "stance": "neutral",
            "sentiment_score": 0.0,
            "narrative_direction": "stable",
            "attention_level": "normal",
            "crowding_risk": False,
        },
    ),
    (
        AdversarialAgentInput,
        {
            **BASE_INPUT,
            "specialist_outputs": {
                "fundamental": {"stance": "neutral"},
                "technical": {"stance": "neutral"},
            },
        },
    ),
    (
        BullBearDecisionMemo,
        {
            **BASE_OUTPUT,
            "bull_case": "Upside case.",
            "bear_case": "Downside case.",
            "base_case": "Balanced case.",
        },
    ),
    (RiskAgentInput, {**BASE_INPUT, "limit_metrics": {"position_weight": 0.05}}),
    (
        RiskAgentOutput,
        {
            **BASE_OUTPUT,
            "disposition": "pass",
            "approved": True,
            "risk_budget_impact": "within budget",
        },
    ),
    (
        PMAgentInput,
        {**BASE_INPUT, "agent_outputs": {"risk": {"disposition": "pass"}}},
    ),
    (
        PMRecommendation,
        {
            **BASE_OUTPUT,
            "action": "hold",
            "conviction": 60,
            "time_horizon": "medium_term",
            "portfolio_fit": "Within mandate.",
            "capital_allocation_guidance": "No change before review.",
        },
    ),
)


@pytest.mark.parametrize(("schema", "payload"), CONTRACT_CASES)
def test_every_agent_contract_accepts_its_versioned_minimum(
    schema: type[BaseModel],
    payload: dict,
) -> None:
    validated = schema.model_validate(payload)

    assert validated.model_dump(mode="json")
    assert schema.model_json_schema()["additionalProperties"] is False


@pytest.mark.parametrize(("schema", "payload"), CONTRACT_CASES)
def test_every_agent_contract_rejects_unknown_fields(
    schema: type[BaseModel],
    payload: dict,
) -> None:
    invalid = deepcopy(payload)
    invalid["unreviewed_payload"] = "must not cross the boundary"

    with pytest.raises(ValidationError) as exc_info:
        schema.model_validate(invalid)

    assert any(error["type"] == "extra_forbidden" for error in exc_info.value.errors())


@pytest.mark.parametrize(
    ("schema", "payload", "field"),
    (
        (
            MacroAgentOutput,
            {**dict(CONTRACT_CASES[1][1]), "regime_probability": 1.01},
            "regime_probability",
        ),
        (
            SentimentAgentOutput,
            {**dict(CONTRACT_CASES[7][1]), "sentiment_score": -1.01},
            "sentiment_score",
        ),
        (PMRecommendation, {**dict(CONTRACT_CASES[13][1]), "conviction": 100.01}, "conviction"),
    ),
)
def test_bounded_agent_scores_reject_out_of_range_values(
    schema: type[BaseModel],
    payload: dict,
    field: str,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        schema.model_validate(payload)

    assert any(field in error["loc"] for error in exc_info.value.errors())
