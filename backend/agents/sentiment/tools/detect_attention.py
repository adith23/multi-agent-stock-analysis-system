from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ml.attention.attention_detector import NewsAttentionDetector


@tool
def detect_attention(article_counts: list[float]) -> dict[str, Any]:
    """Detect unusual attention, news bursts, and crowding risk."""

    return NewsAttentionDetector().predict({"article_counts": article_counts})
