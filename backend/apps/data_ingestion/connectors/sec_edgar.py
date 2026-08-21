from __future__ import annotations

from typing import Any

from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    DataCategory,
    SourceType,
)

from .base import BaseConnector


class SecEdgarConnector(BaseConnector):
    source_type = SourceType.SEC_EDGAR
    supported_categories = frozenset(
        {DataCategory.FILING, DataCategory.INSIDER_TRANSACTION, DataCategory.OWNERSHIP}
    )

    def _company(self, identifier: str):
        if self._client is not None:
            return self._client
        identity = self.config.get("identity")
        if not identity:
            raise ConnectorConfigurationError("SEC_EDGAR_IDENTITY is required")
        from edgar import Company, set_identity

        set_identity(identity)
        return Company(identifier)

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        identifier = str(params.get("cik") or params.get("symbol") or "")
        if params.get("health_check"):
            return [{"status": "configured"}]
        if not identifier:
            raise ValueError("symbol or cik is required")
        company = self._company(identifier)
        form = params.get("form")
        if not form:
            form = {
                DataCategory.FILING: ["10-K", "10-Q", "8-K"],
                DataCategory.INSIDER_TRANSACTION: "4",
                DataCategory.OWNERSHIP: "13F-HR",
            }[category]
        filings = company.get_filings(form=form)
        latest = filings.latest(int(params.get("limit", 20)))
        if hasattr(latest, "to_dict"):
            converted = latest.to_dict()
            if isinstance(converted, dict):
                keys = list(converted)
                if keys and all(isinstance(converted[key], dict) for key in keys):
                    rows = []
                    indexes = set().union(*(converted[key] for key in keys))
                    for index in indexes:
                        rows.append({key: converted[key].get(index) for key in keys})
                    return rows
        return self.as_records(latest)
