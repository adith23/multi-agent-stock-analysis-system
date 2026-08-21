from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizedRecordData

from .base import BaseNormalizationAdapter


class GenericAdapter(BaseNormalizationAdapter):
    """Lossless normalization for source-neutral reference payloads."""

    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        symbol = entity_identifier.upper()
        source_id = str(self.first(payload, "id", "accessionNumber", "uuid", "symbol", default=""))
        source_timestamp = self.datetime(
            self.first(payload, "timestamp", "date", "period_end", "periodEndDate")
        )
        key_parts = (
            category,
            symbol,
            source_id or (source_timestamp.isoformat() if source_timestamp else "latest"),
        )
        return [
            NormalizedRecordData(
                category=DataCategory(category),
                source_type=source_type,
                source_id=source_id,
                entity_identifier=symbol,
                source_timestamp=source_timestamp,
                payload={"symbol": symbol, **payload},
                canonical_key=":".join(key_parts),
            )
        ]
