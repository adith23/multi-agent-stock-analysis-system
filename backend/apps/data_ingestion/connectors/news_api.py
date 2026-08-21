from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    DataCategory,
    SourceType,
)

from .base import BaseConnector


class NewsApiConnector(BaseConnector):
    source_type = SourceType.NEWS_API
    supported_categories = frozenset({DataCategory.NEWS})

    @property
    def client(self):
        if self._client is None:
            api_key = self.config.get("api_key")
            if not api_key:
                raise ConnectorConfigurationError("NEWS_API_KEY is required")
            from newsapi import NewsApiClient

            self._client = NewsApiClient(api_key=api_key)
        return self._client

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        query = params.get("query") or params.get("symbol") or "markets"
        if params.get("health_check"):
            return [{"query": query}]
        end = params.get("end") or datetime.now(UTC)
        start = params.get("start") or end - timedelta(days=7)
        response = self.client.get_everything(
            q=query,
            from_param=start.isoformat() if hasattr(start, "isoformat") else start,
            to=end.isoformat() if hasattr(end, "isoformat") else end,
            language=params.get("language", "en"),
            sort_by="publishedAt",
            page_size=min(int(params.get("limit", 100)), 100),
        )
        return self.as_records(response.get("articles", []))
