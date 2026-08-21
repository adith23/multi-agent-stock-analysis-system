from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizationError, NormalizedRecordData

from .base import BaseNormalizationAdapter


class MacroAdapter(BaseNormalizationAdapter):
    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        series_id = str(payload.get("series_id") or entity_identifier).upper()
        observed_at = self.datetime(self.first(payload, "date", "observed_at"))
        if not series_id or observed_at is None:
            raise NormalizationError("macro record requires series_id and observation date")
        normalized = {
            "series_id": series_id,
            "observed_at": observed_at.date().isoformat(),
            "value": payload.get("value"),
            "title": payload.get("title", ""),
            "frequency": payload.get("frequency", ""),
            "unit": self.first(payload, "unit", "units", default=""),
        }
        return [
            NormalizedRecordData(
                category=DataCategory.MACRO,
                source_type=source_type,
                entity_identifier=series_id,
                source_timestamp=observed_at,
                payload=normalized,
                canonical_key=f"macro:{series_id}:{observed_at.date().isoformat()}",
            )
        ]
