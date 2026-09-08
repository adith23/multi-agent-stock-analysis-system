from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction

from apps.data_ingestion.connectors import connector_registry
from apps.data_ingestion.domain import DataCategory
from apps.market_data.models import SecurityAlias, SecurityType, Ticker

from .ingestion_service import IngestionService
from .source_routing_service import SourceRoutingService


class SecurityResolutionError(LookupError):
    """Raised when configured reference providers cannot verify a security."""


@dataclass(frozen=True, slots=True)
class ResolvedSecurity:
    symbol: str
    exchange: str
    name: str
    currency: str
    security_type: str
    provider_symbol: str
    provider_exchange: str
    provider_instrument_id: str


class _PreloadedConnector:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def fetch_with_resilience(self, category: str, **params: Any) -> list[dict[str, Any]]:
        return self.records


class SecurityResolutionService:
    """Resolve unknown symbols through an enabled company-reference provider."""

    SUPPORTED_TYPES = {
        "ADR": SecurityType.ADR,
        "COMMONSTOCK": SecurityType.EQUITY,
        "EQUITY": SecurityType.EQUITY,
        "ETF": SecurityType.ETF,
        "FUND": SecurityType.FUND,
        "INDEX": SecurityType.INDEX,
        "MUTUALFUND": SecurityType.FUND,
        "STOCK": SecurityType.EQUITY,
    }

    def __init__(
        self,
        *,
        router: SourceRoutingService | None = None,
        ingestion: IngestionService | None = None,
        registry=connector_registry,
    ) -> None:
        self.router = router or SourceRoutingService()
        self.ingestion = ingestion or IngestionService()
        self.registry = registry

    def resolve(self, symbol: str, exchange: str = "US") -> Ticker:
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_exchange = self._normalize_exchange(exchange)
        existing = (
            Ticker.objects.active()
            .filter(symbol=normalized_symbol, exchange=normalized_exchange)
            .first()
        )
        if existing is not None:
            return existing

        aliased = (
            SecurityAlias.objects.select_related("ticker")
            .filter(
                provider_symbol=normalized_symbol,
                ticker__exchange=normalized_exchange,
                ticker__is_active=True,
            )
            .first()
        )
        if aliased is not None:
            return aliased.ticker

        attempts: list[str] = []
        verified: tuple[Any, list[dict[str, Any]], ResolvedSecurity] | None = None
        for config in self.router.candidates(DataCategory.COMPANY_PROFILE):
            try:
                if not self.router.reserve_rate_limit(config):
                    attempts.append(f"{config.source_type}: rate limit exhausted")
                    continue
                connector = self.registry.create(
                    config.source_type,
                    self.ingestion._connector_config(config),
                )
                records = connector.fetch_with_resilience(
                    DataCategory.COMPANY_PROFILE,
                    symbol=normalized_symbol,
                )
                resolved = self._parse_reference(
                    records,
                    requested_symbol=normalized_symbol,
                    requested_exchange=normalized_exchange,
                )
                verified = (config, records, resolved)
                break
            except Exception as exc:
                attempts.append(f"{config.source_type}: {type(exc).__name__}: {exc}")

        if verified is not None:
            config, records, resolved = verified
            ticker = self._persist(resolved, provider=config.source_type)
            self.ingestion.ingest(
                config,
                DataCategory.COMPANY_PROFILE,
                connector=_PreloadedConnector(records),
                ticker=ticker,
                symbol=resolved.provider_symbol,
                exchange=ticker.exchange,
            )
            return ticker

        detail = "; ".join(attempts) if attempts else "no configured reference provider"
        raise SecurityResolutionError(
            f"Unable to verify {normalized_symbol}:{normalized_exchange} ({detail})."
        )

    @classmethod
    def _parse_reference(
        cls,
        records: list[dict[str, Any]],
        *,
        requested_symbol: str,
        requested_exchange: str,
    ) -> ResolvedSecurity:
        if not records:
            raise ValueError("provider returned no company profile")
        payload = records[0]
        provider_symbol = (
            str(payload.get("ticker") or payload.get("symbol") or payload.get("Symbol") or "")
            .strip()
            .upper()
        )
        if not provider_symbol or not cls._symbols_equivalent(provider_symbol, requested_symbol):
            raise ValueError("provider response did not match the requested symbol")
        name = str(
            payload.get("name")
            or payload.get("longName")
            or payload.get("shortName")
            or payload.get("Name")
            or ""
        ).strip()
        if not name:
            raise ValueError("provider response did not contain an official security name")
        currency = str(payload.get("currency") or payload.get("Currency") or "USD").upper()
        provider_exchange = (
            str(
                payload.get("exchange")
                or payload.get("fullExchangeName")
                or payload.get("Exchange")
                or requested_exchange
            )
            .strip()
            .upper()
        )
        raw_type = (
            str(
                payload.get("quoteType")
                or payload.get("assetType")
                or payload.get("AssetType")
                or "EQUITY"
            )
            .replace("_", "")
            .replace(" ", "")
            .upper()
        )
        security_type = cls.SUPPORTED_TYPES.get(raw_type)
        if security_type is None:
            raise ValueError(f"unsupported security type: {raw_type}")
        instrument_id = str(
            payload.get("figi")
            or payload.get("shareClassFIGI")
            or payload.get("isin")
            or payload.get("cik")
            or payload.get("CIK")
            or ""
        ).strip()
        return ResolvedSecurity(
            symbol=requested_symbol,
            exchange=requested_exchange,
            name=name,
            currency=currency,
            security_type=security_type,
            provider_symbol=provider_symbol,
            provider_exchange=provider_exchange,
            provider_instrument_id=instrument_id,
        )

    @staticmethod
    @transaction.atomic
    def _persist(resolved: ResolvedSecurity, *, provider: str) -> Ticker:
        ticker, _ = Ticker.objects.update_or_create(
            symbol=resolved.symbol,
            exchange=resolved.exchange,
            defaults={
                "name": resolved.name,
                "currency": resolved.currency,
                "security_type": resolved.security_type,
                "is_active": True,
            },
        )
        ticker.mark_verified(str(provider))
        ticker.save(
            update_fields=(
                "is_verified",
                "verification_source",
                "verified_at",
                "updated_at",
            )
        )
        SecurityAlias.objects.update_or_create(
            provider=str(provider),
            provider_symbol=resolved.provider_symbol,
            provider_exchange=resolved.provider_exchange,
            defaults={
                "ticker": ticker,
                "provider_instrument_id": resolved.provider_instrument_id,
            },
        )
        return ticker

    @staticmethod
    def _normalize_symbol(value: str) -> str:
        symbol = value.strip().upper()
        if not symbol:
            raise SecurityResolutionError("A ticker symbol is required.")
        return symbol

    @staticmethod
    def _normalize_exchange(value: str) -> str:
        return value.strip().upper() or "US"

    @staticmethod
    def _symbols_equivalent(left: str, right: str) -> bool:
        normalize = lambda value: value.upper().replace(".", "-")  # noqa: E731
        return normalize(left) == normalize(right)
