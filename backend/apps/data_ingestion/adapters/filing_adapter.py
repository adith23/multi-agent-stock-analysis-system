from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizationError, NormalizedRecordData

from .base import BaseNormalizationAdapter


class FilingAdapter(BaseNormalizationAdapter):
    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        accession = str(
            self.first(payload, "accession_number", "accessionNumber", "accession_no", default="")
        )
        filed_at = self.datetime(
            self.first(payload, "filing_date", "filingDate", "filed_at", "date")
        )
        form = str(self.first(payload, "form", "form_type", default=""))
        if not accession and not filed_at:
            raise NormalizationError("filing requires an accession number or filing date")
        normalized = {
            "symbol": entity_identifier.upper(),
            "accession_number": accession,
            "form": form,
            "filed_at": filed_at.isoformat() if filed_at else None,
            "period_end": self.first(payload, "period_of_report", "reportDate", "period_end"),
            "primary_document": self.first(
                payload, "primary_document", "primaryDocument", default=""
            ),
            "url": self.first(payload, "url", "filing_url", default=""),
            "content": self.first(payload, "content", "text", default=""),
            "metadata": payload,
        }
        key = accession or f"{form}:{filed_at.isoformat() if filed_at else 'unknown'}"
        return [
            NormalizedRecordData(
                category=DataCategory.FILING,
                source_type=source_type,
                source_id=accession,
                entity_identifier=entity_identifier.upper(),
                source_timestamp=filed_at,
                payload=normalized,
                canonical_key=f"filing:{entity_identifier.upper()}:{key}",
            )
        ]
