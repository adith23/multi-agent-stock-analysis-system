from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from statistics import mean

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.data_ingestion.domain import DataCategory, IngestionStatus, SourceType
from apps.data_ingestion.models import DataSourceConfiguration, NormalizedDataRecord
from apps.market_data.models import Ticker

SOURCE_PREFERENCES: dict[str, tuple[str, ...]] = {
    DataCategory.OHLCV: (
        SourceType.FINNHUB,
        SourceType.ALPHA_VANTAGE,
        SourceType.YFINANCE,
    ),
    DataCategory.COMPANY_PROFILE: (
        SourceType.FINNHUB,
        SourceType.YFINANCE,
        SourceType.ALPHA_VANTAGE,
    ),
    # Finnhub's current connector exposes basic metric series rather than all
    # three canonical statements, so Yahoo is the complete statement source.
    DataCategory.FINANCIAL_STATEMENT: (SourceType.YFINANCE, SourceType.FINNHUB),
    DataCategory.NEWS: (SourceType.FINNHUB, SourceType.NEWS_API),
    DataCategory.FILING: (SourceType.SEC_EDGAR,),
    DataCategory.OWNERSHIP: (SourceType.SEC_EDGAR, SourceType.FINNHUB),
    DataCategory.INSIDER_TRANSACTION: (SourceType.FINNHUB, SourceType.SEC_EDGAR),
    DataCategory.PEER_GROUP: (SourceType.FINNHUB,),
    DataCategory.MACRO: (SourceType.FRED,),
}

SECRET_SETTINGS = {
    SourceType.FINNHUB: "FINNHUB_API_KEY",
    SourceType.FRED: "FRED_API_KEY",
    SourceType.NEWS_API: "NEWS_API_KEY",
    SourceType.ALPHA_VANTAGE: "ALPHA_VANTAGE_API_KEY",
    SourceType.SEC_EDGAR: "SEC_EDGAR_IDENTITY",
}


@dataclass(frozen=True, slots=True)
class RoutedSource:
    config: DataSourceConfiguration
    recent_quality: float


class SourceRoutingService:
    """Select healthy, configured providers using deterministic category policy."""

    health_cooldown = timedelta(minutes=5)

    def candidates(
        self,
        category: str,
        *,
        ticker: Ticker | None = None,
    ) -> list[DataSourceConfiguration]:
        preference = SOURCE_PREFERENCES.get(category, ())
        preference_rank = {str(source): index for index, source in enumerate(preference)}
        now = timezone.now()
        routed: list[RoutedSource] = []
        queryset = DataSourceConfiguration.objects.filter(is_enabled=True).order_by("priority")
        for config in queryset:
            if not config.supports(category):
                continue
            if not self._has_credentials(config):
                continue
            if not self._supports_exchange(config, ticker):
                continue
            if self._is_unhealthy(config, now):
                continue
            if self._rate_limit_exhausted(config, now):
                continue
            routed.append(RoutedSource(config, self._recent_quality(config, category)))
        routed.sort(
            key=lambda item: (
                preference_rank.get(item.config.source_type, len(preference_rank)),
                item.config.priority,
                -item.recent_quality,
                item.config.source_type,
            )
        )
        return [item.config for item in routed]

    @staticmethod
    def reserve_rate_limit(config: DataSourceConfiguration) -> bool:
        now = timezone.now()
        key = SourceRoutingService._rate_key(config, now)
        if cache.add(key, 1, timeout=90):
            return True
        try:
            return cache.incr(key) <= config.requests_per_minute
        except ValueError:
            return cache.add(key, 1, timeout=90)

    @staticmethod
    def _has_credentials(config: DataSourceConfiguration) -> bool:
        setting_name = SECRET_SETTINGS.get(config.source_type)
        return setting_name is None or bool(getattr(settings, setting_name, ""))

    @staticmethod
    def _supports_exchange(
        config: DataSourceConfiguration,
        ticker: Ticker | None,
    ) -> bool:
        supported = {str(value).upper() for value in config.settings.get("exchanges", [])}
        return ticker is None or not supported or ticker.exchange.upper() in supported

    @classmethod
    def _is_unhealthy(cls, config: DataSourceConfiguration, now) -> bool:
        if config.last_failure_at is None:
            return False
        if config.last_success_at and config.last_success_at >= config.last_failure_at:
            return False
        return config.last_failure_at >= now - cls.health_cooldown

    @staticmethod
    def _recent_quality(config: DataSourceConfiguration, category: str) -> float:
        scores = list(
            NormalizedDataRecord.objects.filter(
                source_type=config.source_type,
                data_category=category,
                status=IngestionStatus.ACCEPTED,
                data_quality_score__isnull=False,
            )
            .order_by("-created_at")
            .values_list("data_quality_score", flat=True)[:100]
        )
        return mean(scores) if scores else 0.0

    @staticmethod
    def _rate_key(config: DataSourceConfiguration, now) -> str:
        return f"ingestion-rate:{config.source_type}:{now:%Y%m%d%H%M}"

    @classmethod
    def _rate_limit_exhausted(cls, config: DataSourceConfiguration, now) -> bool:
        return int(cache.get(cls._rate_key(config, now), 0)) >= config.requests_per_minute
