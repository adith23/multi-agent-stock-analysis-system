from datetime import UTC, datetime
from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizationError, NormalizedRecordData

from .base import BaseNormalizationAdapter


class NewsAdapter(BaseNormalizationAdapter):
    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        nested_content = payload.get("content")
        if isinstance(nested_content, dict):
            payload = {**payload, **nested_content}
        headline = str(self.first(payload, "headline", "title", default="")).strip()
        if not headline:
            raise NormalizationError("news record requires a headline")
        published_at = self.datetime(
            self.first(payload, "datetime", "publishedAt", "providerPublishTime")
        ) or datetime.now(UTC)
        publisher = self.first(payload, "source", "publisher", default="")
        if isinstance(publisher, dict):
            publisher = publisher.get("name", "")
        url_value = self.first(payload, "url", "link", "canonicalUrl", default="")
        if isinstance(url_value, dict):
            url_value = url_value.get("url", "")
        url = str(url_value)
        normalized = {
            "symbols": [entity_identifier.upper()] if entity_identifier else [],
            "headline": headline,
            "summary": self.first(payload, "summary", "description", default="") or "",
            "body": self.first(payload, "content", "body", default="") or "",
            "url": url,
            "publisher": publisher or "",
            "author": payload.get("author") or "",
            "published_at": published_at.isoformat(),
            "language": payload.get("language", "en"),
            "categories": payload.get("category", payload.get("categories", [])),
        }
        return [
            NormalizedRecordData(
                category=DataCategory.NEWS,
                source_type=source_type,
                source_id=str(self.first(payload, "id", "uuid", default=url)),
                entity_identifier=entity_identifier.upper(),
                source_timestamp=published_at,
                payload=normalized,
                canonical_key=f"news:{url or headline.lower()}",
            )
        ]
