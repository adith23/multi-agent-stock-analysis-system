from __future__ import annotations

from collections.abc import Mapping

from apps.data_ingestion.adapters import (
    FilingAdapter,
    GenericAdapter,
    MacroAdapter,
    NewsAdapter,
    OwnershipAdapter,
    PriceAdapter,
)
from apps.data_ingestion.domain import DataCategory, NormalizedRecordData


class NormalizationService:
    """Select the appropriate anti-corruption adapter by data category."""

    def __init__(self, adapters: Mapping[str, object] | None = None) -> None:
        self._adapters = dict(
            adapters
            or {
                DataCategory.QUOTE: PriceAdapter(),
                DataCategory.OHLCV: PriceAdapter(),
                DataCategory.FILING: FilingAdapter(),
                DataCategory.MACRO: MacroAdapter(),
                DataCategory.NEWS: NewsAdapter(),
                DataCategory.OWNERSHIP: OwnershipAdapter(),
                DataCategory.INSIDER_TRANSACTION: OwnershipAdapter(),
                DataCategory.COMPANY_PROFILE: GenericAdapter(),
                DataCategory.FINANCIAL_STATEMENT: GenericAdapter(),
                DataCategory.PEER_GROUP: GenericAdapter(),
                DataCategory.ALTERNATIVE: GenericAdapter(),
            }
        )

    def normalize(
        self,
        payload: dict,
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        from apps.data_ingestion.domain import UnsupportedDataTypeError

        adapter = self._adapters.get(category)
        if adapter is None:
            raise UnsupportedDataTypeError(f"No normalization adapter for {category}")
        return adapter.normalize(
            payload,
            source_type=source_type,
            category=category,
            entity_identifier=entity_identifier,
        )
