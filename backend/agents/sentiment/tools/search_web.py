from __future__ import annotations

from typing import Any

import httpx
from django.conf import settings
from langchain_core.tools import tool

from apps.core.domain.exceptions import ConfigurationError


@tool
def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search configured public web sources through Tavily; never accesses private data."""

    api_key = getattr(settings, "TAVILY_API_KEY", "")
    if not api_key:
        raise ConfigurationError("TAVILY_API_KEY is required for public web search")
    response = httpx.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max(1, min(max_results, 10)),
            "search_depth": "basic",
        },
        timeout=20.0,
    )
    response.raise_for_status()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
            "score": item.get("score"),
        }
        for item in response.json().get("results", [])
    ]
