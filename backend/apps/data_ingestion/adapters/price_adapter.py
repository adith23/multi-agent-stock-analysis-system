from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apps.data_ingestion.domain import DataCategory, NormalizationError, NormalizedRecordData

from .base import BaseNormalizationAdapter


class PriceAdapter(BaseNormalizationAdapter):
    def normalize(
        self,
        payload: dict[str, Any],
        *,
        source_type: str,
        category: str,
        entity_identifier: str = "",
    ) -> list[NormalizedRecordData]:
        symbol = str(self.first(payload, "symbol", "ticker", default=entity_identifier)).upper()
        if category == DataCategory.QUOTE:
            timestamp = self.datetime(self.first(payload, "t", "timestamp")) or datetime.now(UTC)
            price = self.first(payload, "c", "current_price", "regularMarketPrice", "close")
            if price is None:
                raise NormalizationError("quote does not contain a current price")
            normalized = {
                "symbol": symbol,
                "timestamp": timestamp.isoformat(),
                "price": price,
                "open": self.first(payload, "o", "open", "regularMarketOpen"),
                "high": self.first(payload, "h", "high", "dayHigh"),
                "low": self.first(payload, "l", "low", "dayLow"),
                "previous_close": self.first(payload, "pc", "previous_close", "previousClose"),
            }
            return [
                NormalizedRecordData(
                    category=DataCategory.QUOTE,
                    source_type=source_type,
                    entity_identifier=symbol,
                    source_timestamp=timestamp,
                    payload=normalized,
                    canonical_key=f"quote:{symbol}:{timestamp.isoformat()}",
                )
            ]

        timestamps = payload.get("t")
        if isinstance(timestamps, list):
            return [
                self._bar(
                    symbol,
                    timestamps[index],
                    payload["o"][index],
                    payload["h"][index],
                    payload["l"][index],
                    payload["c"][index],
                    payload["v"][index],
                    payload.get("interval", "1d"),
                    source_type,
                    adjusted_close=(
                        payload.get("adjusted_close", [None] * len(timestamps))[index]
                    ),
                )
                for index in range(len(timestamps))
            ]
        return [
            self._bar(
                symbol,
                self.first(payload, "timestamp", "date", "datetime"),
                self.first(payload, "open", "Open"),
                self.first(payload, "high", "High"),
                self.first(payload, "low", "Low"),
                self.first(payload, "close", "Close"),
                self.first(payload, "volume", "Volume", default=0),
                self.first(payload, "interval", default="1d"),
                source_type,
                adjusted_close=self.first(payload, "adjusted_close", "adj_close", "Adj Close"),
            )
        ]

    def _bar(
        self,
        symbol: str,
        timestamp_value: Any,
        open_value: Any,
        high: Any,
        low: Any,
        close: Any,
        volume: Any,
        interval: str,
        source_type: str,
        *,
        adjusted_close: Any = None,
    ) -> NormalizedRecordData:
        if any(value is None for value in (timestamp_value, open_value, high, low, close)):
            raise NormalizationError("OHLCV record is missing a required field")
        timestamp = self.datetime(timestamp_value)
        assert timestamp is not None
        payload = {
            "symbol": symbol,
            "timestamp": timestamp.isoformat(),
            "interval": interval,
            "open": open_value,
            "high": high,
            "low": low,
            "close": close,
            "adjusted_close": adjusted_close,
            "volume": volume or 0,
        }
        return NormalizedRecordData(
            category=DataCategory.OHLCV,
            source_type=source_type,
            entity_identifier=symbol,
            source_timestamp=timestamp,
            payload=payload,
            canonical_key=f"ohlcv:{symbol}:{interval}:{timestamp.isoformat()}",
        )
