from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.adversarial.graph import build_adversarial_agent_graph
from agents.fundamental.graph import build_fundamental_agent_graph
from agents.macro.graph import build_macro_agent_graph
from agents.pm.graph import build_pm_agent_graph
from agents.risk.graph import build_risk_agent_graph
from agents.sentiment.graph import build_sentiment_agent_graph
from agents.supervisor.nodes import (
    join_specialists,
    make_adversarial_node,
    make_pm_node,
    make_risk_node,
    make_specialist_node,
    mark_risk_blocked,
    prepare,
)
from agents.supervisor.routing import route_after_risk
from agents.supervisor.state import SupervisorState
from agents.technical.graph import build_technical_agent_graph
from llm.providers.registry import get_llm


def build_supervisor_graph(
    *,
    llm: Any | None = None,
    checkpointer: Any = None,
):
    """Build parallel specialists → adversarial → risk → HITL PM orchestration."""

    model = llm or get_llm(temperature=0.2)
    builder = StateGraph(SupervisorState)
    builder.add_node("prepare", prepare)
    builder.add_node(
        "macro",
        make_specialist_node("macro", build_macro_agent_graph, llm=model),
    )
    builder.add_node(
        "fundamental",
        make_specialist_node("fundamental", build_fundamental_agent_graph, llm=model),
    )
    builder.add_node(
        "technical",
        make_specialist_node("technical", build_technical_agent_graph, llm=model),
    )
    builder.add_node(
        "sentiment",
        make_specialist_node("sentiment", build_sentiment_agent_graph, llm=model),
    )
    builder.add_node("join_specialists", join_specialists)
    builder.add_node(
        "adversarial",
        make_adversarial_node(build_adversarial_agent_graph, llm=model),
    )
    builder.add_node("risk", make_risk_node(build_risk_agent_graph, llm=model))
    builder.add_node("risk_blocked", mark_risk_blocked)
    builder.add_node("pm", make_pm_node(build_pm_agent_graph, llm=model))

    builder.add_edge(START, "prepare")
    for agent_id in ("macro", "fundamental", "technical", "sentiment"):
        builder.add_edge("prepare", agent_id)
    builder.add_edge(
        ["macro", "fundamental", "technical", "sentiment"],
        "join_specialists",
    )
    builder.add_edge("join_specialists", "adversarial")
    builder.add_edge("adversarial", "risk")
    builder.add_conditional_edges(
        "risk",
        route_after_risk,
        {"review": "pm", "blocked": "risk_blocked"},
    )
    builder.add_edge("risk_blocked", "pm")
    builder.add_edge("pm", END)
    return builder.compile(checkpointer=checkpointer, interrupt_before=["pm"])
