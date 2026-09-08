"""Read repository for canonical market-data projections."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from apps.market_data.models import (
    CompanyProfile,
    FinancialStatement,
    MacroIndicator,
    NewsItem,
    OHLCVBar,
    Ticker,
)


class MarketDataRepository:
    def macro_observations(
        self,
        series_ids: list[str],
        *,
        per_series_limit: int = 24,
        as_of=None,
        available_as_of=None,
        source_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        queryset = MacroIndicator.objects.filter(series_id__in=series_ids)
        if source_types:
            queryset = queryset.filter(source_type__in=source_types)
        if as_of is not None:
            queryset = queryset.filter(
                observed_at__lte=as_of.date(),
            )
        availability_cutoff = available_as_of or as_of
        if availability_cutoff is not None:
            queryset = queryset.filter(available_at__lte=availability_cutoff)
        rows = queryset.order_by("series_id", "-observed_at").values(
            "series_id",
            "title",
            "observed_at",
            "value",
            "frequency",
            "unit",
            "source_id",
        )
        counts: dict[str, int] = {}
        result = []
        for row in rows:
            series_id = str(row["series_id"])
            counts[series_id] = counts.get(series_id, 0) + 1
            if counts[series_id] <= per_series_limit:
                result.append(row)
        return result

    def financial_statements(
        self,
        ticker: Ticker | str,
        *,
        limit: int = 12,
        as_of=None,
        available_as_of=None,
        source_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        queryset = FinancialStatement.objects.filter(**self._ticker_filter(ticker))
        if source_types:
            queryset = queryset.filter(source_type__in=source_types)
        if as_of is not None:
            queryset = queryset.filter(period_end__lte=as_of.date())
        availability_cutoff = available_as_of or as_of
        if availability_cutoff is not None:
            queryset = queryset.filter(available_at__lte=availability_cutoff)
        return list(
            queryset.order_by("-period_end").values(
                "statement_type",
                "period_end",
                "fiscal_year",
                "fiscal_quarter",
                "currency",
                "values",
                "source_id",
                "source_timestamp",
            )[:limit]
        )

    def company_profile(
        self,
        ticker: Ticker | str,
        *,
        as_of=None,
        available_as_of=None,
        source_types: list[str] | None = None,
    ) -> dict[str, Any]:
        queryset = CompanyProfile.objects.filter(**self._ticker_filter(ticker))
        if source_types:
            queryset = queryset.filter(source_type__in=source_types)
        availability_cutoff = available_as_of or as_of
        if availability_cutoff is not None:
            queryset = queryset.filter(available_at__lte=availability_cutoff)
        return (
            queryset.order_by("-available_at")
            .values(
                "legal_name",
                "description",
                "website",
                "headquarters_country",
                "market_cap",
                "shares_outstanding",
                "attributes",
                "source_id",
            )
            .first()
            or {}
        )

    def price_bars(
        self,
        ticker: Ticker | str,
        *,
        interval: str = "1d",
        limit: int = 252,
        as_of=None,
        available_as_of=None,
        source_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        queryset = OHLCVBar.objects.filter(
            interval=interval,
            **self._ticker_filter(ticker),
        )
        if source_types:
            queryset = queryset.filter(source_type__in=source_types)
        if as_of is not None:
            queryset = queryset.filter(timestamp__lte=as_of)
        availability_cutoff = available_as_of or as_of
        if availability_cutoff is not None:
            queryset = queryset.filter(available_at__lte=availability_cutoff)
        rows = list(
            queryset.order_by("-timestamp").values(
                "timestamp", "open", "high", "low", "close", "volume", "source_id"
            )[:limit]
        )
        return list(reversed(rows))

    def news(
        self,
        ticker: Ticker | str,
        *,
        lookback_days: int = 30,
        limit: int = 100,
        as_of=None,
        available_as_of=None,
        source_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        as_of = as_of or timezone.now()
        availability_cutoff = available_as_of or as_of
        source_filter = {"source_type__in": source_types} if source_types else {}
        return list(
            NewsItem.objects.filter(
                **self._ticker_filter(ticker),
                **source_filter,
                published_at__gte=as_of - timedelta(days=lookback_days),
                published_at__lte=as_of,
                available_at__lte=availability_cutoff,
            )
            .order_by("-published_at")
            .values(
                "headline",
                "summary",
                "url",
                "publisher",
                "published_at",
                "sentiment_score",
                "categories",
                "source_id",
            )[:limit]
        )

    @staticmethod
    def _ticker_filter(ticker: Ticker | str) -> dict[str, Any]:
        if isinstance(ticker, Ticker):
            return {"ticker": ticker}
        return {"ticker__symbol": ticker.strip().upper()}
