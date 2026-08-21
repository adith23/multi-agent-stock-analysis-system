from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizationError, NormalizedRecordData

from .base import BaseNormalizationAdapter


class OwnershipAdapter(BaseNormalizationAdapter):
    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        items = payload.get("data") if isinstance(payload.get("data"), list) else [payload]
        records: list[NormalizedRecordData] = []
        for item in items:
            transaction_at = self.datetime(
                self.first(item, "transactionDate", "transaction_date", "filingDate", "date")
            )
            owner = str(
                self.first(item, "name", "ownerName", "owner_name", "investorName", default="")
            )
            if not owner and transaction_at is None:
                raise NormalizationError("ownership record requires owner or transaction date")
            normalized_category = (
                DataCategory.INSIDER_TRANSACTION
                if category == DataCategory.INSIDER_TRANSACTION
                else DataCategory.OWNERSHIP
            )
            normalized = {
                "symbol": entity_identifier.upper(),
                "owner_name": owner,
                "owner_relationship": self.first(item, "relationship", "officerTitle", default=""),
                "transaction_date": (
                    transaction_at.date().isoformat() if transaction_at else None
                ),
                "transaction_code": self.first(
                    item, "transactionCode", "transaction_code", default=""
                ),
                "shares": self.first(item, "share", "shares", "change", default=None),
                "price": self.first(item, "transactionPrice", "price", default=None),
                "value": self.first(item, "value", default=None),
                "is_direct_ownership": self.first(item, "isDirect", "direct", default=None),
                "accession_number": self.first(
                    item, "accessionNumber", "accession_number", default=""
                ),
                "metadata": item,
            }
            key = (
                f"{normalized_category}:{entity_identifier.upper()}:{owner}:"
                f"{normalized['transaction_date']}:{normalized['transaction_code']}"
            )
            records.append(
                NormalizedRecordData(
                    category=normalized_category,
                    source_type=source_type,
                    entity_identifier=entity_identifier.upper(),
                    source_timestamp=transaction_at,
                    payload=normalized,
                    canonical_key=key,
                )
            )
        return records
