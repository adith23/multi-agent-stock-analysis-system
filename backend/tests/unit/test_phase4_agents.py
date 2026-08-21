from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from agents.adversarial.graph import build_adversarial_agent_graph
from agents.adversarial.memory import AdversarialMemory
from agents.base.registry import AgentRegistry, register_default_agents
from agents.fundamental.graph import build_fundamental_agent_graph
from agents.fundamental.memory import FundamentalMemory
from agents.macro.graph import build_macro_agent_graph
from agents.macro.memory import MacroMemory
from agents.pm.graph import build_pm_agent_graph
from agents.pm.memory import PMMemory
from agents.pm.tools import compute_position_size, rank_ideas
from agents.risk.graph import build_risk_agent_graph
from agents.risk.memory import RiskMemory
from agents.sentiment.graph import build_sentiment_agent_graph
from agents.sentiment.memory import SentimentMemory
from agents.supervisor.graph import build_supervisor_graph
from agents.technical.graph import build_technical_agent_graph
from agents.technical.memory import TechnicalMemory
from apps.market_data.repositories import MarketDataRepository
from apps.research.repositories import ResearchRepository
from apps.signals.repositories import SignalRepository


class StubStructuredModel:
    def __init__(self, schema: type) -> None:
        self.schema = schema

    def invoke(self, messages: list[Any]):
        return self.schema.model_validate(deepcopy(STRUCTURED_OUTPUTS[self.schema.__name__]))


class StubLLM:
    def with_structured_output(self, schema: type) -> StubStructuredModel:
        return StubStructuredModel(schema)


BASE_OUTPUT = {
    "summary": "Evidence-supported summary.",
    "rationale": "The supplied deterministic outputs support this conclusion.",
    "confidence": 0.72,
    "evidence": [],
    "assumptions": ["Inputs remain current."],
    "limitations": ["No forecast is guaranteed."],
}

STRUCTURED_OUTPUTS = {
    "MacroAgentOutput": {
        **BASE_OUTPUT,
        "regime": "risk_on",
        "regime_probability": 0.8,
        "transition_detected": False,
        "equity_impact": "bullish",
    },
    "FundamentalAgentOutput": {
        **BASE_OUTPUT,
        "stance": "bullish",
        "thesis": "Cash generation and balance-sheet quality support the thesis.",
        "quality_assessment": "good",
        "moat_assessment": "moderate",
        "management_assessment": "credible",
    },
    "TechnicalAgentOutput": {
        **BASE_OUTPUT,
        "stance": "bullish",
        "trend_state": "uptrend",
        "timing_cue": "enter",
        "momentum_state": "balanced",
        "relative_strength_view": "outperforming",
    },
    "SentimentAgentOutput": {
        **BASE_OUTPUT,
        "stance": "neutral",
        "sentiment_score": 0.1,
        "narrative_direction": "stable",
        "attention_level": "normal",
        "crowding_risk": False,
    },
    "DebateArgument": {
        "thesis": "The position has a testable case.",
        "claims": ["Claim supported by supplied reports."],
    },
    "ModeratorDecision": {
        "verdict": "conclude",
        "rationale": "Material disagreements are fully framed.",
    },
    "BullBearDecisionMemo": {
        **BASE_OUTPUT,
        "bull_case": "Upside case.",
        "bear_case": "Downside case.",
        "base_case": "Balanced base case.",
    },
    "RiskAgentOutput": {
        **BASE_OUTPUT,
        "disposition": "pass",
        "approved": True,
        "risk_budget_impact": "within budget",
    },
    "PMRecommendation": {
        **BASE_OUTPUT,
        "action": "buy",
        "conviction": 70,
        "time_horizon": "medium_term",
        "portfolio_fit": "Fits the configured mandate.",
        "capital_allocation_guidance": "Initiate within the approved risk budget.",
    },
}


@pytest.fixture
def ohlcv() -> list[dict[str, float]]:
    return [
        {
            "open": 99.0 + index,
            "high": 101.0 + index,
            "low": 98.0 + index,
            "close": 100.0 + index,
            "volume": 1_000.0 + index * 10,
        }
        for index in range(40)
    ]


def initial_state(agent_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [],
        "analysis_run_id": "00000000-0000-0000-0000-000000000001",
        "ticker": "TEST",
        "input_data": agent_input,
        "trace": [],
    }


def test_specialist_graphs_are_independently_invocable(ohlcv):
    llm = StubLLM()
    graphs_and_inputs = [
        (
            build_macro_agent_graph(llm=llm),
            {
                "macro_indicators": [{"series_id": "GDP", "value": 2.0}],
                "regime_output": {"regime": "risk_on", "probability": 0.8},
                "yield_curve": {"3m": 4.0, "2y": 4.2, "10y": 4.5},
            },
            "macro",
        ),
        (
            build_fundamental_agent_graph(llm=llm),
            {"financials": {"revenue": 100}, "company_profile": {"name": "Test Inc."}},
            "fundamental",
        ),
        (
            build_technical_agent_graph(llm=llm),
            {"ohlcv": ohlcv, "benchmark_prices": [90 + index for index in range(40)]},
            "technical",
        ),
        (
            build_sentiment_agent_graph(llm=llm),
            {
                "news": [{"headline": "Test headline", "source_id": "news-1"}],
                "sentiment_results": [
                    {"sentiment": "neutral", "confidence": 0.8, "scores": {"neutral": 0.8}}
                ],
                "article_counts": [1, 1, 2, 1, 2, 1, 1, 2, 1, 2],
            },
            "sentiment",
        ),
        (
            build_risk_agent_graph(llm=llm),
            {"limit_metrics": {"position_weight": 0.05}},
            "risk",
        ),
    ]

    for graph, payload, expected_agent in graphs_and_inputs:
        result = graph.invoke(initial_state(payload))
        assert result["agent_output"]["metadata"]["agent_id"] == expected_agent
        assert result["trace"][-1] == f"{expected_agent}.analyze"


def test_adversarial_graph_executes_bounded_cycle():
    graph = build_adversarial_agent_graph(llm=StubLLM())
    state = initial_state({"max_debate_rounds": 3})
    state.update(
        {
            "specialist_outputs": {
                "fundamental": {"stance": "bullish"},
                "technical": {"stance": "neutral"},
            },
            "debate_round": 0,
            "bull_arguments": [],
            "bear_arguments": [],
        }
    )

    result = graph.invoke(state)

    assert result["debate_round"] == 1
    assert len(result["bull_arguments"]) == 1
    assert len(result["bear_arguments"]) == 1
    assert result["agent_output"]["metadata"]["agent_id"] == "adversarial"


def test_pm_graph_pauses_for_review_and_resumes():
    graph = build_pm_agent_graph(llm=StubLLM(), checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "pm-review-1"}}
    result = graph.invoke(
        initial_state(
            {
                "agent_outputs": {
                    "fundamental": {"stance": "bullish"},
                    "risk": {"disposition": "block"},
                },
                "conviction": {"score": 70},
            }
        ),
        config=config,
    )
    assert "agent_output" not in result
    assert graph.get_state(config).next == ("human_review",)
    assert result["draft_recommendation"]["action"] == "not_buy"

    graph.update_state(
        config,
        {
            "human_decision": {
                "decision": "approve",
                "rationale": "Reviewed and accepted.",
                "reviewer_id": "pm-1",
            }
        },
    )
    completed = graph.invoke(None, config=config)

    assert completed["agent_output"]["decision_status"] == "approved"
    assert completed["agent_output"]["human_review"]["reviewer_id"] == "pm-1"


def test_supervisor_fans_out_joins_and_pauses_before_pm(ohlcv):
    graph = build_supervisor_graph(llm=StubLLM(), checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "supervisor-1"}}
    state = {
        "messages": [],
        "analysis_run_id": "00000000-0000-0000-0000-000000000002",
        "ticker": "TEST",
        "parallel_results": [],
        "agent_inputs": {
            "macro": {"regime_output": {"regime": "risk_on", "probability": 0.8}},
            "fundamental": {"financials": {"revenue": 100}},
            "technical": {"ohlcv": ohlcv},
            "sentiment": {"sentiment_results": []},
            "adversarial": {"max_debate_rounds": 1},
            "risk": {"limit_metrics": {"position_weight": 0.05}},
            "pm": {"conviction": {"score": 70}},
        },
        "trace": [],
    }

    paused = graph.invoke(state, config=config)

    assert set(paused["specialist_outputs"]) == {
        "macro",
        "fundamental",
        "technical",
        "sentiment",
    }
    assert graph.get_state(config).next == ("pm",)
    graph.update_state(
        config,
        {
            "human_decision": {
                "decision": "approve",
                "rationale": "Portfolio review complete.",
                "reviewer_id": "pm-2",
            }
        },
    )
    completed = graph.invoke(None, config=config)
    assert completed["current_stage"] == "completed"
    assert completed["agent_output"]["decision_status"] == "approved"


def test_registry_and_pm_deterministic_tools():
    register_default_agents()
    assert {
        "adversarial",
        "fundamental",
        "macro",
        "pm",
        "risk",
        "sentiment",
        "supervisor",
        "technical",
    } <= set(AgentRegistry.available())
    sizing = compute_position_size.invoke(
        {
            "methodology": "fixed_fractional",
            "inputs": {
                "fraction": 0.02,
                "conviction": 75,
                "volatility": 0.2,
                "liquidity": 1.0,
                "correlation": 0.2,
                "risk_budget": 1.0,
                "portfolio_value": 1_000_000,
                "price": 100,
            },
        }
    )
    assert sizing["methodology"] == "fixed_fractional"

    ranked = rank_ideas.invoke(
        {
            "ideas": [
                {"ticker": "AAA", "return": 0.2, "risk": 0.1},
                {"ticker": "BBB", "return": 0.1, "risk": 0.2},
            ],
            "criteria": ["return", "risk"],
            "weights": [0.7, 0.3],
            "beneficial": [True, False],
        }
    )
    assert ranked[0]["ticker"] == "AAA"


@pytest.mark.django_db
def test_agent_memory_and_data_repositories_are_isolated_read_adapters():
    market = MarketDataRepository()
    research = ResearchRepository()
    signals = SignalRepository()
    run_id = "00000000-0000-0000-0000-000000000009"

    assert market.macro_observations(["GDP"]) == []
    assert market.financial_statements("TEST") == []
    assert market.company_profile("TEST") == {}
    assert market.price_bars("TEST") == []
    assert market.news("TEST") == []
    assert research.specialist_reports_for_run(run_id) == []
    assert research.recent_specialist_reports("TEST", "fundamental") == []
    assert research.recent_decision_memos("TEST") == []
    assert signals.recent_regimes() == []
    assert signals.recent_technical_signals("TEST") == []

    for memory in (
        MacroMemory(),
        FundamentalMemory(),
        TechnicalMemory(),
        SentimentMemory(),
        AdversarialMemory(),
        RiskMemory(),
        PMMemory(),
    ):
        assert memory.recent("TEST") == []
