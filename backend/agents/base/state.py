"""Typed state shared by all LangGraph agent subgraphs."""

from __future__ import annotations

import operator
from typing import Annotated, Any, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    analysis_run_id: str
    ticker: str
    input_data: NotRequired[dict[str, Any]]
    tool_outputs: NotRequired[dict[str, Any]]
    agent_output: NotRequired[dict[str, Any]]
    error: NotRequired[str | None]
    warnings: NotRequired[list[str]]
    trace: NotRequired[list[str]]


class AnalysisState(AgentState):
    """Supervisor-level state that aggregates specialist results."""

    specialist_outputs: NotRequired[dict[str, dict[str, Any]]]
    parallel_results: NotRequired[Annotated[list[dict[str, Any]], operator.add]]
    current_stage: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]
