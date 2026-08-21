from __future__ import annotations

from typing import Any

from agents.base.memory import AgentMemory
from agents.base.runtime import attach_metadata, invoke_structured
from agents.sentiment.prompts import ANALYSIS_TASK, PROMPT_VERSION, SYSTEM_PROMPT
from agents.sentiment.schemas import SentimentAgentInput, SentimentAgentOutput
from agents.sentiment.state import SentimentAgentState
from agents.sentiment.tools import classify_sentiment, detect_attention

AGENT_ID = "sentiment"
AGENT_VERSION = "1.0.0"


def make_prepare_node(memory: AgentMemory):
    def prepare(state: SentimentAgentState) -> dict[str, Any]:
        payload = SentimentAgentInput.model_validate(
            {
                "analysis_run_id": state["analysis_run_id"],
                "ticker": state["ticker"],
                **state.get("input_data", {}),
            }
        )
        data = payload.model_dump(mode="json")
        texts = data["texts"] or [
            f"{item.get('headline', '')}. {item.get('summary', '')}".strip()
            for item in data["news"]
            if item.get("headline")
        ]
        sentiment = data["sentiment_results"]
        if sentiment is None:
            sentiment = classify_sentiment.invoke({"texts": texts}) if texts else []
        attention = (
            detect_attention.invoke({"article_counts": data["article_counts"]})
            if data["article_counts"]
            else {}
        )
        return {
            "news": data["news"],
            "sentiment_results": sentiment,
            "attention": attention,
            "prior_context": memory.recent(state["ticker"]),
            "tool_outputs": {"sentiment": sentiment, "attention": attention},
            "trace": [*state.get("trace", []), "sentiment.prepare"],
        }

    return prepare


def make_analyze_node(llm: Any):
    def analyze(state: SentimentAgentState) -> dict[str, Any]:
        output = invoke_structured(
            llm,
            SentimentAgentOutput,
            system_prompt=SYSTEM_PROMPT,
            task=ANALYSIS_TASK,
            context={
                "ticker": state["ticker"],
                "news": state.get("news", []),
                "finbert": state.get("sentiment_results", []),
                "attention": state.get("attention", {}),
                "prior_sentiment": state.get("prior_context", []),
            },
        )
        return {
            "agent_output": attach_metadata(
                output,
                agent_id=AGENT_ID,
                agent_version=AGENT_VERSION,
                prompt_version=PROMPT_VERSION,
            ),
            "trace": [*state.get("trace", []), "sentiment.analyze"],
        }

    return analyze
