from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db.models import Min
from django.utils import timezone

from apps.data_ingestion.domain import DataCategory, IngestionStatus
from apps.data_ingestion.models import (
    DataPreparationRun,
    DataPreparationStatus,
    NormalizedDataRecord,
)
from apps.market_data.models import (
    CompanyProfile,
    FinancialStatement,
    MacroIndicator,
    NewsItem,
    OHLCVBar,
    PeerGroup,
    StatementType,
)
from apps.orchestrator.models import AnalysisRun

from .tasks_defaults import DEFAULT_MACRO_SERIES


class DataReadinessError(RuntimeError):
    pass


class AnalysisDataReadinessService:
    """Plan and validate the point-in-time data required by an analysis."""

    required_categories = (
        DataCategory.OHLCV,
        DataCategory.COMPANY_PROFILE,
        DataCategory.FINANCIAL_STATEMENT,
        DataCategory.MACRO,
    )
    degradable_categories = (DataCategory.NEWS,)

    def create_plan(self, run: AnalysisRun) -> DataPreparationRun:
        knowledge_limit = run.data_cutoff_at if run.is_historical else timezone.now()
        entries: dict[str, dict[str, Any]] = {}
        cache_hits: list[str] = []
        categories = [*self.required_categories, *self.degradable_categories]
        categories.extend(self._enabled_optional_categories())
        for category in categories:
            inspection = self.inspect_category(run, category, knowledge_limit=knowledge_limit)
            fetch = not inspection["fresh"] and not run.is_historical
            entry = {
                "category": str(category),
                "required": category in self.required_categories
                or category in self._required_optional_categories(),
                "fetch": fetch,
                "inspection": inspection,
                "parameter_sets": self._parameter_sets(run, category),
            }
            entries[str(category)] = entry
            if inspection["fresh"]:
                cache_hits.append(str(category))
        preparation, _ = DataPreparationRun.objects.update_or_create(
            analysis_run=run,
            defaults={
                "ticker": run.ticker,
                "status": DataPreparationStatus.PENDING,
                "requested_categories": categories,
                "plan": entries,
                "cache_hits": cache_hits,
                "source_attempts": [],
                "fallbacks": [],
                "category_results": {},
                "selected_sources": {},
                "warnings": [],
                "errors": [],
                "started_at": None,
                "completed_at": None,
            },
        )
        return preparation

    def evaluate(self, run: AnalysisRun, *, knowledge_cutoff=None) -> dict[str, Any]:
        knowledge_cutoff = knowledge_cutoff or timezone.now()
        inspections: dict[str, dict[str, Any]] = {}
        failures: list[str] = []
        warnings: list[str] = []
        selected_sources: dict[str, list[str]] = {}
        preparation = getattr(run, "data_preparation", None)
        plan = preparation.plan if preparation is not None else {}
        categories = list(plan) or [
            *self.required_categories,
            *self.degradable_categories,
            *self._enabled_optional_categories(),
        ]
        for category in categories:
            inspection = self.inspect_category(
                run,
                category,
                knowledge_limit=knowledge_cutoff,
            )
            inspections[str(category)] = inspection
            selected_sources[str(category)] = inspection.pop("sources")
            required = plan.get(str(category), {}).get(
                "required",
                category in self.required_categories,
            )
            if required and not inspection["gate_ready"]:
                failures.extend(f"{category}: {issue}" for issue in inspection["issues"])
            elif not inspection["fresh"]:
                warnings.extend(f"{category}: {issue}" for issue in inspection["issues"])
        status = (
            DataPreparationStatus.FAILED
            if failures
            else DataPreparationStatus.DEGRADED
            if warnings
            else DataPreparationStatus.READY
        )
        return {
            "status": status,
            "categories": inspections,
            "selected_sources": selected_sources,
            "warnings": warnings,
            "errors": failures,
            "knowledge_cutoff_at": knowledge_cutoff,
        }

    def inspect_category(
        self,
        run: AnalysisRun,
        category: str,
        *,
        knowledge_limit,
    ) -> dict[str, Any]:
        handlers = {
            DataCategory.OHLCV: self._inspect_ohlcv,
            DataCategory.COMPANY_PROFILE: self._inspect_profile,
            DataCategory.FINANCIAL_STATEMENT: self._inspect_financials,
            DataCategory.NEWS: self._inspect_news,
            DataCategory.MACRO: self._inspect_macro,
            DataCategory.PEER_GROUP: self._inspect_peers,
        }
        handler = handlers.get(category, self._inspect_normalized)
        return handler(run, category, knowledge_limit)

    def _inspect_ohlcv(self, run, category, knowledge_limit) -> dict[str, Any]:
        minimum = int(getattr(settings, "ANALYSIS_MINIMUM_OHLCV_BARS", 200))
        desired_days = int(getattr(settings, "ANALYSIS_DESIRED_OHLCV_DAYS", 730))
        base_queryset = OHLCVBar.objects.filter(
            ticker=run.ticker,
            interval="1d",
            timestamp__lte=run.data_cutoff_at,
            available_at__lte=knowledge_limit,
        )
        selected = None
        for source in self._ordered_sources(base_queryset, category):
            queryset = base_queryset.filter(source_type=source)
            count = queryset.count()
            latest = queryset.order_by("-timestamp").first()
            oldest = queryset.order_by("timestamp").first()
            issues: list[str] = []
            if count < minimum:
                issues.append(f"requires at least {minimum} daily bars; found {count}")
            latest_is_fresh = bool(
                latest is not None
                and run.data_cutoff_at - latest.timestamp <= timedelta(days=4)
            )
            if not latest_is_fresh:
                issues.append("latest daily bar is stale")
            desired_start = run.data_cutoff_at - timedelta(days=desired_days)
            desired_coverage = oldest is not None and oldest.timestamp <= desired_start
            if not desired_coverage:
                issues.append(f"does not cover the desired {desired_days}-day window")
            quality = queryset.aggregate(value=Min("data_quality_score"))["value"]
            quality_ok = quality is not None and quality >= self._minimum_quality()
            if not quality_ok:
                issues.append("minimum source data quality was not met")
            gate_ready = count >= minimum and latest_is_fresh and quality_ok
            inspection = self._inspection(
                fresh=gate_ready and desired_coverage,
                gate_ready=gate_ready,
                issues=issues,
                sources=[source],
                metrics={"count": count, "minimum": minimum, "minimum_quality": quality},
            )
            if inspection["fresh"]:
                return inspection
            if selected is None or count > selected[0]:
                selected = (count, inspection)
        if selected is not None:
            return selected[1]
        return self._inspection(
            fresh=False,
            gate_ready=False,
            issues=[f"requires at least {minimum} daily bars; found 0"],
            sources=[],
            metrics={"count": 0, "minimum": minimum, "minimum_quality": None},
        )

    def _inspect_profile(self, run, category, knowledge_limit) -> dict[str, Any]:
        profile = CompanyProfile.objects.filter(
            ticker=run.ticker,
            available_at__lte=knowledge_limit,
        ).order_by("-available_at").first()
        issues = []
        if profile is None:
            issues.append("company profile is missing")
        elif not profile.legal_name:
            issues.append("company profile has no legal name")
        quality_ok = bool(
            profile
            and profile.data_quality_score is not None
            and profile.data_quality_score >= self._minimum_quality()
        )
        if profile and not quality_ok:
            issues.append("company profile quality is below threshold")
        max_age = timedelta(days=int(getattr(settings, "ANALYSIS_PROFILE_MAX_AGE_DAYS", 30)))
        fresh = bool(profile and quality_ok and knowledge_limit - profile.available_at <= max_age)
        if profile and not fresh:
            issues.append("company profile is stale")
        return self._inspection(
            fresh=fresh and not issues,
            gate_ready=bool(profile and profile.legal_name and quality_ok),
            issues=issues,
            sources=[profile.source_type] if profile else [],
            metrics={"available_at": profile.available_at.isoformat() if profile else None},
        )

    def _inspect_financials(self, run, category, knowledge_limit) -> dict[str, Any]:
        base_queryset = FinancialStatement.objects.filter(
            ticker=run.ticker,
            period_end__lte=run.data_cutoff_at.date(),
            available_at__lte=knowledge_limit,
        )
        expected = {StatementType.INCOME, StatementType.BALANCE_SHEET, StatementType.CASH_FLOW}
        selected = None
        for source in self._ordered_sources(base_queryset, category):
            queryset = base_queryset.filter(source_type=source)
            found = set(queryset.values_list("statement_type", flat=True))
            missing = sorted(str(value) for value in expected - found)
            issues = [f"missing statement types: {', '.join(missing)}"] if missing else []
            quality = queryset.aggregate(value=Min("data_quality_score"))["value"]
            quality_ok = quality is not None and quality >= self._minimum_quality()
            if not quality_ok:
                issues.append("financial statement quality is below threshold")
            currency_mismatch = queryset.exclude(currency=run.ticker.currency).exists()
            if currency_mismatch:
                issues.append("financial statement currency does not match the security")
            latest = queryset.order_by("-period_end").first()
            stale = latest is None or (
                run.data_cutoff_at.date() - latest.period_end > timedelta(days=550)
            )
            if stale:
                issues.append("latest financial statement is stale")
            gate_ready = not missing and quality_ok and not currency_mismatch and not stale
            inspection = self._inspection(
                fresh=gate_ready,
                gate_ready=gate_ready,
                issues=issues,
                sources=[source],
                metrics={"count": queryset.count(), "statement_types": sorted(found)},
            )
            if inspection["fresh"]:
                return inspection
            score = len(found & expected)
            if selected is None or score > selected[0]:
                selected = (score, inspection)
        if selected is not None:
            return selected[1]
        return self._inspection(
            fresh=False,
            gate_ready=False,
            issues=["missing statement types: balance_sheet, cash_flow, income"],
            sources=[],
            metrics={"count": 0, "statement_types": []},
        )

    def _inspect_news(self, run, category, knowledge_limit) -> dict[str, Any]:
        start = run.data_cutoff_at - timedelta(days=30)
        queryset = NewsItem.objects.filter(
            ticker=run.ticker,
            published_at__gte=start,
            published_at__lte=run.data_cutoff_at,
            available_at__lte=knowledge_limit,
        )
        count = queryset.count()
        issues = [] if count else ["no recent news was available"]
        return self._inspection(
            fresh=count > 0,
            gate_ready=True,
            issues=issues,
            sources=queryset.values_list("source_type", flat=True).distinct(),
            metrics={"count": count, "lookback_days": 30},
        )

    def _inspect_macro(self, run, category, knowledge_limit) -> dict[str, Any]:
        series = self._macro_series()
        queryset = MacroIndicator.objects.filter(
            series_id__in=series,
            observed_at__lte=run.data_cutoff_at.date(),
            available_at__lte=knowledge_limit,
        )
        found = set(queryset.values_list("series_id", flat=True))
        missing = sorted(set(series) - found)
        issues = [f"missing macro series: {', '.join(missing)}"] if missing else []
        max_age_days = {
            "GDPC1": 200,
            "FEDFUNDS": 75,
            "CPIAUCSL": 75,
            "UNRATE": 75,
            "DGS10": 10,
            "DGS2": 10,
            "VIXCLS": 10,
        }
        stale = []
        for series_id in found:
            latest = queryset.filter(series_id=series_id).order_by("-observed_at").first()
            if latest and (
                run.data_cutoff_at.date() - latest.observed_at
                > timedelta(days=max_age_days.get(series_id, 90))
            ):
                stale.append(series_id)
        if stale:
            issues.append(f"stale macro series: {', '.join(sorted(stale))}")
        quality = queryset.aggregate(value=Min("data_quality_score"))["value"]
        quality_ok = quality is not None and quality >= self._minimum_quality()
        if queryset.exists() and not quality_ok:
            issues.append("macro data quality is below threshold")
        ready = not missing and not stale and quality_ok
        return self._inspection(
            fresh=ready,
            gate_ready=ready,
            issues=issues,
            sources=queryset.values_list("source_type", flat=True).distinct(),
            metrics={"series": sorted(found), "minimum_quality": quality},
        )

    def _inspect_peers(self, run, category, knowledge_limit) -> dict[str, Any]:
        group = PeerGroup.objects.filter(ticker=run.ticker).order_by("-version").first()
        count = group.peers.count() if group else 0
        issues = [] if count else ["peer group is missing or empty"]
        return self._inspection(
            fresh=count > 0,
            gate_ready=count > 0,
            issues=issues,
            sources=[],
            metrics={"peer_count": count},
        )

    def _inspect_normalized(self, run, category, knowledge_limit) -> dict[str, Any]:
        queryset = NormalizedDataRecord.objects.filter(
            ticker=run.ticker,
            data_category=category,
            status=IngestionStatus.ACCEPTED,
            available_at__lte=knowledge_limit,
        )
        count = queryset.count()
        issues = [] if count else ["no accepted canonical records were available"]
        return self._inspection(
            fresh=count > 0,
            gate_ready=count > 0,
            issues=issues,
            sources=queryset.values_list("source_type", flat=True).distinct(),
            metrics={"count": count},
        )

    @staticmethod
    def _inspection(*, fresh, gate_ready, issues, sources, metrics) -> dict[str, Any]:
        return {
            "fresh": bool(fresh),
            "gate_ready": bool(gate_ready),
            "issues": list(dict.fromkeys(issues)),
            "sources": sorted({str(source) for source in sources if source}),
            "metrics": metrics,
        }

    @staticmethod
    def _minimum_quality() -> float:
        return float(getattr(settings, "ANALYSIS_MINIMUM_DATA_QUALITY", 0.6))

    @staticmethod
    def _macro_series() -> tuple[str, ...]:
        return tuple(getattr(settings, "ANALYSIS_REQUIRED_MACRO_SERIES", DEFAULT_MACRO_SERIES))

    @staticmethod
    def _enabled_optional_categories() -> list[str]:
        return [str(value) for value in getattr(settings, "ANALYSIS_DATA_CAPABILITIES", ())]

    @staticmethod
    def _required_optional_categories() -> set[str]:
        return {
            str(value)
            for value in getattr(settings, "ANALYSIS_REQUIRED_OPTIONAL_DATA_CAPABILITIES", ())
        }

    @staticmethod
    def _ordered_sources(queryset, category: str) -> list[str]:
        from .source_routing_service import SOURCE_PREFERENCES

        preference = {
            str(source): index
            for index, source in enumerate(SOURCE_PREFERENCES.get(category, ()))
        }
        sources = set(queryset.values_list("source_type", flat=True).distinct())
        return sorted(
            sources,
            key=lambda source: (preference.get(source, len(preference)), source),
        )

    def _parameter_sets(self, run: AnalysisRun, category: str) -> list[dict[str, Any]]:
        if category == DataCategory.MACRO:
            return [
                {
                    "series_id": series_id,
                    "end": run.data_cutoff_at.date().isoformat(),
                }
                for series_id in self._macro_series()
            ]
        common = {
            "symbol": run.ticker.symbol,
            "exchange": run.ticker.exchange,
            "end": run.data_cutoff_at.isoformat(),
        }
        if category == DataCategory.OHLCV:
            return [
                {
                    **common,
                    "start": (run.data_cutoff_at - timedelta(days=730)).isoformat(),
                    "period": "2y",
                    "interval": "1d",
                    "resolution": "D",
                }
            ]
        if category == DataCategory.NEWS:
            return [
                {
                    **common,
                    "start": (run.data_cutoff_at - timedelta(days=30)).isoformat(),
                    "limit": 100,
                }
            ]
        return [common]
