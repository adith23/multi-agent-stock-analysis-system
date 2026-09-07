from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime

from apps.data_ingestion.domain import DataCategory
from apps.data_ingestion.models import NormalizedDataRecord
from apps.market_data.models import (
    CompanyProfile,
    FinancialStatement,
    InsiderTransaction,
    MacroIndicator,
    NewsItem,
    OHLCVBar,
    PeerGroup,
    StatementType,
    Ticker,
)


class MarketDataService:
    """Repository-oriented access to the canonical market-data store."""

    @staticmethod
    def resolve_ticker(symbol: str, *, exchange: str = "US") -> Ticker:
        ticker, _ = Ticker.objects.get_or_create(
            symbol=symbol.strip().upper(),
            exchange=exchange.strip().upper(),
        )
        return ticker

    @staticmethod
    def latest_bars(symbol: str, *, interval: str = "1d", limit: int = 252):
        return OHLCVBar.objects.filter(ticker__symbol=symbol.upper(), interval=interval).order_by(
            "-timestamp"
        )[:limit]


class MarketDataProjector:
    """Project accepted normalized records into strongly typed read models."""

    BULK_CATEGORIES = frozenset({DataCategory.OHLCV, DataCategory.MACRO})

    @transaction.atomic
    def project(self, record: NormalizedDataRecord) -> object | None:
        handlers = {
            DataCategory.OHLCV: self._ohlcv,
            DataCategory.COMPANY_PROFILE: self._profile,
            DataCategory.FINANCIAL_STATEMENT: self._financial_statement,
            DataCategory.MACRO: self._macro,
            DataCategory.NEWS: self._news,
            DataCategory.INSIDER_TRANSACTION: self._insider,
            DataCategory.PEER_GROUP: self._peer_group,
        }
        handler = handlers.get(record.data_category)
        return handler(record) if handler else None

    @transaction.atomic
    def project_many(self, records: list[NormalizedDataRecord]) -> list[object]:
        """Project high-volume observations with one database upsert per model.

        Categories without a set-based projector retain the ordinary per-record
        behavior.  Ingestion currently calls this method only for categories in
        ``BULK_CATEGORIES``.
        """
        if not records:
            return []
        categories = {record.data_category for record in records}
        if len(categories) != 1:
            raise ValueError("bulk projection requires records from one category")
        category = categories.pop()
        if category == DataCategory.OHLCV:
            return list(self._ohlcv_many(records))
        if category == DataCategory.MACRO:
            return list(self._macro_many(records))
        return [projected for record in records if (projected := self.project(record)) is not None]

    @staticmethod
    def _provenance(record: NormalizedDataRecord) -> dict[str, Any]:
        return {
            "source_type": record.source_type,
            "source_id": record.source_id,
            "source_timestamp": record.source_timestamp,
            "data_quality_score": record.data_quality_score,
            "content_hash": record.content_hash,
        }

    @staticmethod
    def _ticker(record: NormalizedDataRecord) -> Ticker:
        if record.ticker_id:
            return record.ticker
        return MarketDataService.resolve_ticker(record.entity_identifier)

    def _ohlcv(self, record: NormalizedDataRecord) -> OHLCVBar:
        data = record.normalized_payload
        timestamp = parse_datetime(data["timestamp"])
        assert timestamp is not None
        values = {
            "open": Decimal(str(data["open"])),
            "high": Decimal(str(data["high"])),
            "low": Decimal(str(data["low"])),
            "close": Decimal(str(data["close"])),
            "adjusted_close": (
                Decimal(str(data["adjusted_close"]))
                if data.get("adjusted_close") is not None
                else None
            ),
            "volume": Decimal(str(data.get("volume", 0))),
            **self._provenance(record),
        }
        bar, _ = OHLCVBar.objects.update_or_create(
            ticker=self._ticker(record),
            timestamp=timestamp,
            interval=data.get("interval", "1d"),
            source_type=record.source_type,
            defaults=values,
        )
        return bar

    def _ohlcv_many(self, records: list[NormalizedDataRecord]) -> list[OHLCVBar]:
        bars: list[OHLCVBar] = []
        for record in records:
            data = record.normalized_payload
            timestamp = parse_datetime(data["timestamp"])
            if timestamp is None:
                raise ValueError("canonical OHLCV record requires a valid timestamp")
            bars.append(
                OHLCVBar(
                    ticker=self._ticker(record),
                    timestamp=timestamp,
                    interval=data.get("interval", "1d"),
                    open=Decimal(str(data["open"])),
                    high=Decimal(str(data["high"])),
                    low=Decimal(str(data["low"])),
                    close=Decimal(str(data["close"])),
                    adjusted_close=(
                        Decimal(str(data["adjusted_close"]))
                        if data.get("adjusted_close") is not None
                        else None
                    ),
                    volume=Decimal(str(data.get("volume", 0))),
                    **self._provenance(record),
                )
            )
        OHLCVBar.objects.bulk_create(
            bars,
            batch_size=500,
            update_conflicts=True,
            unique_fields=("ticker", "timestamp", "interval", "source_type"),
            update_fields=(
                "open",
                "high",
                "low",
                "close",
                "adjusted_close",
                "volume",
                "source_id",
                "source_timestamp",
                "data_quality_score",
                "content_hash",
                "updated_at",
            ),
        )
        return bars

    def _profile(self, record: NormalizedDataRecord) -> CompanyProfile:
        data = record.normalized_payload
        profile, _ = CompanyProfile.objects.update_or_create(
            ticker=self._ticker(record),
            source_type=record.source_type,
            content_hash=record.content_hash,
            defaults={
                "legal_name": data.get("name") or data.get("longName", ""),
                "description": data.get("description") or data.get("longBusinessSummary", ""),
                "website": data.get("weburl") or data.get("website", ""),
                "headquarters_country": data.get("country", ""),
                "market_cap": data.get("marketCapitalization") or data.get("marketCap"),
                "shares_outstanding": data.get("shareOutstanding")
                or data.get("sharesOutstanding"),
                "attributes": data,
                **self._provenance(record),
            },
        )
        return profile

    def _financial_statement(self, record: NormalizedDataRecord) -> FinancialStatement:
        data = record.normalized_payload
        period = parse_date(str(data.get("period_end") or data.get("periodEndDate") or ""))
        if period is None:
            raise ValueError("canonical financial statement requires a valid period_end")
        statement_type = str(data.get("statement_type") or "")
        if statement_type not in StatementType.values:
            raise ValueError(f"invalid canonical financial statement type: {statement_type!r}")
        values = data.get("values")
        if not isinstance(values, dict) or not values:
            raise ValueError("canonical financial statement requires non-empty values")
        statement, _ = FinancialStatement.objects.update_or_create(
            ticker=self._ticker(record),
            statement_type=statement_type,
            period_end=period,
            source_type=record.source_type,
            defaults={
                "fiscal_year": int(data.get("fiscal_year", period.year)),
                "fiscal_quarter": data.get("fiscal_quarter"),
                "currency": data.get("currency", "USD"),
                "accession_number": data.get("accession_number", ""),
                "values": values,
                **self._provenance(record),
            },
        )
        return statement

    def _macro(self, record: NormalizedDataRecord) -> MacroIndicator:
        data = record.normalized_payload
        observed_at = parse_date(data["observed_at"])
        assert observed_at is not None
        indicator, _ = MacroIndicator.objects.update_or_create(
            series_id=data["series_id"],
            observed_at=observed_at,
            source_type=record.source_type,
            defaults={
                "title": data.get("title", ""),
                "value": data.get("value"),
                "frequency": data.get("frequency", ""),
                "unit": data.get("unit", ""),
                **self._provenance(record),
            },
        )
        return indicator

    def _macro_many(self, records: list[NormalizedDataRecord]) -> list[MacroIndicator]:
        indicators: list[MacroIndicator] = []
        for record in records:
            data = record.normalized_payload
            observed_at = parse_date(data["observed_at"])
            if observed_at is None:
                raise ValueError("canonical macro record requires a valid observation date")
            indicators.append(
                MacroIndicator(
                    series_id=data["series_id"],
                    observed_at=observed_at,
                    title=data.get("title", ""),
                    value=data.get("value"),
                    frequency=data.get("frequency", ""),
                    unit=data.get("unit", ""),
                    **self._provenance(record),
                )
            )
        MacroIndicator.objects.bulk_create(
            indicators,
            batch_size=500,
            update_conflicts=True,
            unique_fields=("series_id", "observed_at", "source_type"),
            update_fields=(
                "title",
                "value",
                "frequency",
                "unit",
                "source_id",
                "source_timestamp",
                "data_quality_score",
                "content_hash",
                "updated_at",
            ),
        )
        return indicators

    def _news(self, record: NormalizedDataRecord) -> NewsItem:
        data = record.normalized_payload
        published_at = parse_datetime(data["published_at"])
        assert published_at is not None
        item, _ = NewsItem.objects.update_or_create(
            content_hash=record.content_hash,
            source_type=record.source_type,
            defaults={
                "headline": data["headline"],
                "summary": data.get("summary", ""),
                "body": data.get("body", ""),
                "url": data.get("url", ""),
                "publisher": data.get("publisher", ""),
                "author": data.get("author", ""),
                "published_at": published_at,
                "language": data.get("language", "en"),
                "categories": data.get("categories") or [],
                "ticker": (
                    record.ticker
                    or MarketDataService.resolve_ticker(
                        (data.get("symbols") or [record.entity_identifier])[0]
                    )
                    if (data.get("symbols") or [record.entity_identifier])[0]
                    else None
                ),
                **self._provenance(record),
            },
        )
        return item

    def _insider(self, record: NormalizedDataRecord) -> InsiderTransaction:
        data = record.normalized_payload
        transaction_date = parse_date(data["transaction_date"])
        assert transaction_date is not None
        item, _ = InsiderTransaction.objects.update_or_create(
            ticker=self._ticker(record),
            content_hash=record.content_hash,
            source_type=record.source_type,
            defaults={
                "owner_name": data["owner_name"],
                "owner_relationship": data.get("owner_relationship", ""),
                "transaction_date": transaction_date,
                "transaction_code": data.get("transaction_code", ""),
                "shares": data.get("shares"),
                "price": data.get("price"),
                "value": data.get("value"),
                "is_direct_ownership": data.get("is_direct_ownership"),
                "accession_number": data.get("accession_number", ""),
                **self._provenance(record),
            },
        )
        return item

    def _peer_group(self, record: NormalizedDataRecord) -> PeerGroup:
        data = record.normalized_payload
        group, _ = PeerGroup.objects.update_or_create(
            ticker=self._ticker(record),
            name=data.get("name", f"{record.entity_identifier} peers"),
            version=1,
            defaults={"methodology": data.get("methodology", "source-provided peers")},
        )
        group.peers.set(
            MarketDataService.resolve_ticker(
                symbol,
                exchange=record.ticker.exchange if record.ticker_id else "US",
            )
            for symbol in data.get("peers", [])
            if symbol and symbol != record.entity_identifier
        )
        return group
