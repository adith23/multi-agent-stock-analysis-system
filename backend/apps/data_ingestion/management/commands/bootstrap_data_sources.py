from django.core.management.base import BaseCommand

from apps.data_ingestion.domain import DataCategory, SourceType
from apps.data_ingestion.models import DataSourceConfiguration
from apps.data_ingestion.tasks import FRED_SERIES

DEFAULTS = {
    SourceType.FINNHUB: {
        "display_name": "Finnhub",
        "priority": 10,
        "supported_categories": [
            DataCategory.QUOTE,
            DataCategory.OHLCV,
            DataCategory.COMPANY_PROFILE,
            DataCategory.FINANCIAL_STATEMENT,
            DataCategory.NEWS,
            DataCategory.PEER_GROUP,
            DataCategory.INSIDER_TRANSACTION,
            DataCategory.OWNERSHIP,
        ],
        "settings": {"symbols": []},
    },
    SourceType.FRED: {
        "display_name": "FRED",
        "priority": 20,
        "supported_categories": [DataCategory.MACRO],
        "settings": {"series_ids": list(FRED_SERIES)},
    },
    SourceType.SEC_EDGAR: {
        "display_name": "SEC EDGAR",
        "priority": 20,
        "supported_categories": [
            DataCategory.FILING,
            DataCategory.INSIDER_TRANSACTION,
            DataCategory.OWNERSHIP,
        ],
        "settings": {"symbols": []},
        "requests_per_minute": 10,
    },
    SourceType.NEWS_API: {
        "display_name": "NewsAPI",
        "priority": 30,
        "supported_categories": [DataCategory.NEWS],
        "settings": {"symbols": [], "queries": []},
    },
    SourceType.YFINANCE: {
        "display_name": "Yahoo Finance fallback",
        "priority": 100,
        "supported_categories": [
            DataCategory.QUOTE,
            DataCategory.OHLCV,
            DataCategory.COMPANY_PROFILE,
            DataCategory.FINANCIAL_STATEMENT,
            DataCategory.NEWS,
        ],
        "settings": {"symbols": []},
    },
    SourceType.ALPHA_VANTAGE: {
        "display_name": "Alpha Vantage fallback",
        "priority": 90,
        "supported_categories": [
            DataCategory.QUOTE,
            DataCategory.OHLCV,
            DataCategory.COMPANY_PROFILE,
        ],
        "settings": {"symbols": []},
    },
}


class Command(BaseCommand):
    help = "Create or update safe, disabled-by-default public data-source policies."

    def handle(self, *args, **options) -> None:
        for source_type, defaults in DEFAULTS.items():
            _, created = DataSourceConfiguration.objects.update_or_create(
                source_type=source_type,
                defaults={**defaults, "is_enabled": False},
            )
            action = "created" if created else "updated"
            self.stdout.write(f"{action}: {source_type}")
