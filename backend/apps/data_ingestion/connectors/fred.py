from __future__ import annotations

from typing import Any

from apps.data_ingestion.domain import (
    ConnectorConfigurationError,
    DataCategory,
    SourceType,
)

from .base import BaseConnector


class FredConnector(BaseConnector):
    source_type = SourceType.FRED
    supported_categories = frozenset({DataCategory.MACRO})

    @property
    def client(self):
        if self._client is None:
            api_key = self.config.get("api_key")
            if not api_key:
                raise ConnectorConfigurationError("FRED_API_KEY is required")
            from fredapi import Fred

            self._client = Fred(api_key=api_key)
        return self._client

    def fetch(self, category: str, **params: Any) -> list[dict[str, Any]]:
        series_id = str(params.get("series_id", "FEDFUNDS")).upper()
        if params.get("health_check"):
            return [{"series_id": series_id}]
        series = self.client.get_series(
            series_id,
            observation_start=params.get("start"),
            observation_end=params.get("end"),
        )
        info = self.client.get_series_info(series_id)
        return [
            {
                "series_id": series_id,
                "date": index.isoformat(),
                "value": None if value != value else value,
                "title": getattr(info, "title", "") if info is not None else "",
                "frequency": getattr(info, "frequency", "") if info is not None else "",
                "units": getattr(info, "units", "") if info is not None else "",
            }
            for index, value in series.items()
        ]
