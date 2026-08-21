from __future__ import annotations

import threading
from collections.abc import Mapping
from typing import Any

from apps.data_ingestion.domain import ConnectorConfigurationError, SourceType

from .base import BaseConnector


class ConnectorRegistry:
    """Thread-safe abstract factory for data-source connectors."""

    def __init__(self) -> None:
        self._connectors: dict[str, type[BaseConnector]] = {}
        self._lock = threading.RLock()

    def register(
        self, source_type: SourceType | str, connector_class: type[BaseConnector]
    ) -> None:
        key = str(source_type)
        with self._lock:
            existing = self._connectors.get(key)
            if existing is not None and existing is not connector_class:
                raise ValueError(f"A connector is already registered for {key}")
            self._connectors[key] = connector_class

    def create(
        self,
        source_type: SourceType | str,
        config: Mapping[str, Any] | None = None,
        **dependencies: Any,
    ) -> BaseConnector:
        key = str(source_type)
        with self._lock:
            connector_class = self._connectors.get(key)
        if connector_class is None:
            raise ConnectorConfigurationError(f"No connector is registered for {key}")
        return connector_class(config, **dependencies)

    def available_sources(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._connectors))


connector_registry = ConnectorRegistry()


def register_defaults() -> None:
    from .alpha_vantage import AlphaVantageConnector
    from .finnhub import FinnhubConnector
    from .fred import FredConnector
    from .news_api import NewsApiConnector
    from .sec_edgar import SecEdgarConnector
    from .yfinance import YFinanceConnector

    for connector_class in (
        FinnhubConnector,
        FredConnector,
        SecEdgarConnector,
        NewsApiConnector,
        YFinanceConnector,
        AlphaVantageConnector,
    ):
        connector_registry.register(connector_class.source_type, connector_class)


register_defaults()
