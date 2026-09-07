from __future__ import annotations

from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.utils import timezone

from apps.data_ingestion.domain import DataCategory, IngestionBatchResult, SourceType
from apps.data_ingestion.models import (
    DataPreparationRun,
    DataPreparationStatus,
    DataSourceConfiguration,
)
from apps.data_ingestion.services import (
    AnalysisDataReadinessService,
    AnalysisIngestionService,
    SecurityResolutionError,
    SecurityResolutionService,
)
from apps.market_data.models import (
    CompanyProfile,
    FinancialStatement,
    MacroIndicator,
    OHLCVBar,
    SecurityAlias,
    StatementType,
    Ticker,
)
from apps.market_data.repositories import MarketDataRepository
from apps.orchestrator.models import AnalysisRun

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="readiness-user",
        email="readiness@example.com",
        password="test-password",
    )


class StubRouter:
    def __init__(self, configs) -> None:
        self.configs = configs

    def candidates(self, category, *, ticker=None):
        return self.configs

    @staticmethod
    def reserve_rate_limit(config) -> bool:
        return True


class StubRegistry:
    def __init__(self, records) -> None:
        self.connector = Mock()
        self.connector.fetch_with_resilience.return_value = records

    def create(self, source_type, config):
        return self.connector


def _source_config() -> DataSourceConfiguration:
    return DataSourceConfiguration.objects.create(
        source_type=SourceType.YFINANCE,
        display_name="Yahoo reference",
        is_enabled=True,
        supported_categories=[DataCategory.COMPANY_PROFILE],
    )


def test_security_resolver_verifies_unknown_symbol_and_persists_alias() -> None:
    config = _source_config()
    records = [
        {
            "symbol": "BRK-B",
            "longName": "Berkshire Hathaway Inc.",
            "currency": "USD",
            "exchange": "NYQ",
            "quoteType": "EQUITY",
            "shareClassFIGI": "BBG001S90346",
        }
    ]
    ingestion = Mock()
    resolver = SecurityResolutionService(
        router=StubRouter([config]),
        ingestion=ingestion,
        registry=StubRegistry(records),
    )

    ticker = resolver.resolve(" brk.b ", " us ")

    assert ticker.symbol == "BRK.B"
    assert ticker.exchange == "US"
    assert ticker.name == "Berkshire Hathaway Inc."
    assert ticker.is_verified is True
    assert ticker.verification_source == SourceType.YFINANCE
    alias = SecurityAlias.objects.get(ticker=ticker)
    assert alias.provider_symbol == "BRK-B"
    assert alias.provider_exchange == "NYQ"
    assert alias.provider_instrument_id == "BBG001S90346"
    ingestion.ingest.assert_called_once()


def test_security_resolver_does_not_persist_unverified_symbol() -> None:
    config = _source_config()
    resolver = SecurityResolutionService(
        router=StubRouter([config]),
        ingestion=Mock(),
        registry=StubRegistry([]),
    )

    with pytest.raises(SecurityResolutionError, match="Unable to verify"):
        resolver.resolve("UNKNOWN", "US")

    assert not Ticker.objects.filter(symbol="UNKNOWN").exists()


def _complete_canonical_data(run: AnalysisRun) -> None:
    now = timezone.now()
    bars = []
    for index in range(200):
        age_days = (199 - index) * 730 / 199
        timestamp = run.data_cutoff_at - timedelta(days=age_days)
        bars.append(
            OHLCVBar(
                ticker=run.ticker,
                timestamp=timestamp,
                open=100,
                high=101,
                low=99,
                close=100,
                volume=1_000,
                source_type="test",
                source_timestamp=timestamp,
                available_at=now,
                data_quality_score=0.95,
                content_hash=f"{index:064d}",
            )
        )
    OHLCVBar.objects.bulk_create(bars)
    CompanyProfile.objects.create(
        ticker=run.ticker,
        legal_name="Acme Corporation",
        source_type="test",
        available_at=now,
        data_quality_score=0.95,
        content_hash="a" * 64,
    )
    for index, statement_type in enumerate(
        (StatementType.INCOME, StatementType.BALANCE_SHEET, StatementType.CASH_FLOW)
    ):
        FinancialStatement.objects.create(
            ticker=run.ticker,
            statement_type=statement_type,
            period_end=run.data_cutoff_at.date() - timedelta(days=90),
            fiscal_year=run.data_cutoff_at.year,
            currency="USD",
            values={"value": 1},
            source_type="test",
            available_at=now,
            data_quality_score=0.95,
            content_hash=f"statement-{index}".ljust(64, "0"),
        )
    macro_ages = {
        "FEDFUNDS": 30,
        "CPIAUCSL": 30,
        "GDPC1": 90,
        "UNRATE": 30,
        "DGS10": 2,
        "DGS2": 2,
        "VIXCLS": 2,
    }
    for index, (series_id, age) in enumerate(macro_ages.items()):
        MacroIndicator.objects.create(
            series_id=series_id,
            observed_at=run.data_cutoff_at.date() - timedelta(days=age),
            value=1,
            source_type="test",
            available_at=now,
            data_quality_score=0.95,
            content_hash=f"macro-{index}".ljust(64, "0"),
        )


def test_readiness_plan_uses_cache_and_degrades_only_for_optional_news(user) -> None:
    ticker = Ticker.objects.create(
        symbol="ACME",
        exchange="US",
        name="Acme",
        currency="USD",
    )
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id="readiness-complete",
        data_cutoff_at=timezone.now() - timedelta(days=1),
    )
    _complete_canonical_data(run)
    service = AnalysisDataReadinessService()

    preparation = service.create_plan(run)
    evaluation = service.evaluate(run, knowledge_cutoff=timezone.now())

    assert set(preparation.cache_hits) >= {
        DataCategory.OHLCV,
        DataCategory.COMPANY_PROFILE,
        DataCategory.FINANCIAL_STATEMENT,
        DataCategory.MACRO,
    }
    assert preparation.plan[DataCategory.NEWS]["fetch"] is True
    assert evaluation["status"] == DataPreparationStatus.DEGRADED
    assert not evaluation["errors"]
    assert any("no recent news" in warning for warning in evaluation["warnings"])


def test_historical_plan_never_fetches_missing_current_data(user) -> None:
    ticker = Ticker.objects.create(symbol="OLD", exchange="US", name="Historical")
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id="readiness-historical",
        data_cutoff_at=timezone.now() - timedelta(days=365),
        is_historical=True,
    )

    preparation = AnalysisDataReadinessService().create_plan(run)

    assert preparation.plan
    assert all(not entry["fetch"] for entry in preparation.plan.values())


def test_finalization_freezes_knowledge_cutoff_and_auditable_manifest(user) -> None:
    ticker = Ticker.objects.create(
        symbol="SNAP",
        exchange="US",
        name="Snapshot Corp",
        currency="USD",
    )
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id="readiness-snapshot",
        data_cutoff_at=timezone.now() - timedelta(days=1),
    )
    _complete_canonical_data(run)
    AnalysisDataReadinessService().create_plan(run)

    result = AnalysisIngestionService().finalize(str(run.id))

    run.refresh_from_db()
    run.data_preparation.refresh_from_db()
    assert result["status"] == DataPreparationStatus.DEGRADED
    assert run.knowledge_cutoff_at is not None
    assert run.knowledge_cutoff_at > run.data_cutoff_at
    assert run.run_manifest["observation_cutoff_at"] == str(run.data_cutoff_at)
    assert run.run_manifest["knowledge_cutoff_at"] is not None
    assert run.run_manifest["data_preparation"]["status"] == DataPreparationStatus.DEGRADED


def test_repository_uses_canonical_ticker_identity_for_duplicate_symbols() -> None:
    now = timezone.now()
    us = Ticker.objects.create(symbol="ABC", exchange="US", name="US security")
    ca = Ticker.objects.create(symbol="ABC", exchange="CA", name="Canadian security")
    for ticker, close in ((us, 10), (ca, 20)):
        OHLCVBar.objects.create(
            ticker=ticker,
            timestamp=now - timedelta(days=1),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=100,
            source_type="test",
            source_timestamp=now,
            data_quality_score=1,
            content_hash=str(close).ljust(64, "0"),
        )

    rows = MarketDataRepository().price_bars(us, as_of=now, available_as_of=now)

    assert len(rows) == 1
    assert float(rows[0]["close"]) == 10.0


def test_repository_selects_profile_known_at_snapshot_cutoff() -> None:
    now = timezone.now()
    ticker = Ticker.objects.create(symbol="PIT", exchange="US", name="Point In Time")
    old_available_at = now - timedelta(days=2)
    CompanyProfile.objects.create(
        ticker=ticker,
        legal_name="Original Name",
        source_type="test",
        available_at=old_available_at,
        data_quality_score=1,
        content_hash="old-profile".ljust(64, "0"),
    )
    CompanyProfile.objects.create(
        ticker=ticker,
        legal_name="Future Rename",
        source_type="test",
        available_at=now,
        data_quality_score=1,
        content_hash="new-profile".ljust(64, "0"),
    )

    profile = MarketDataRepository().company_profile(
        ticker,
        as_of=now,
        available_as_of=old_available_at,
    )

    assert profile["legal_name"] == "Original Name"


def test_concurrent_lock_windows_are_stable_across_request_microseconds() -> None:
    first = AnalysisIngestionService._lock_parameters(
        DataCategory.OHLCV,
        {
            "symbol": "AAPL",
            "exchange": "US",
            "start": "2024-09-07T10:00:00.123456+00:00",
            "end": "2026-09-07T10:00:00.123456+00:00",
            "interval": "1d",
        },
    )
    second = AnalysisIngestionService._lock_parameters(
        DataCategory.OHLCV,
        {
            "symbol": "AAPL",
            "exchange": "US",
            "start": "2024-09-07T10:00:01.999999+00:00",
            "end": "2026-09-07T10:00:01.999999+00:00",
            "interval": "1d",
        },
    )

    assert first == second


def test_ingestion_uses_fallback_and_records_provider_attempts(user) -> None:
    ticker = Ticker.objects.create(symbol="FALL", exchange="US", name="Fallback Corp")
    run = AnalysisRun.objects.create(
        ticker=ticker,
        initiated_by=user,
        checkpoint_thread_id="readiness-fallback",
    )
    primary = DataSourceConfiguration.objects.create(
        source_type=SourceType.FINNHUB,
        display_name="Primary",
        is_enabled=True,
        supported_categories=[DataCategory.OHLCV],
    )
    fallback = DataSourceConfiguration.objects.create(
        source_type=SourceType.YFINANCE,
        display_name="Fallback",
        is_enabled=True,
        supported_categories=[DataCategory.OHLCV],
    )
    preparation = DataPreparationRun.objects.create(
        analysis_run=run,
        ticker=ticker,
        status=DataPreparationStatus.RUNNING,
        requested_categories=[DataCategory.OHLCV],
        plan={
            DataCategory.OHLCV: {
                "category": DataCategory.OHLCV,
                "required": True,
                "fetch": True,
                "parameter_sets": [{"symbol": ticker.symbol, "interval": "1d"}],
            }
        },
    )
    router = StubRouter([primary, fallback])
    ingestion = Mock()
    ingestion.ingest.side_effect = [
        IngestionBatchResult(
            source=SourceType.FINNHUB,
            category=DataCategory.OHLCV,
            failed=1,
            errors=["provider unavailable"],
        ),
        IngestionBatchResult(
            source=SourceType.YFINANCE,
            category=DataCategory.OHLCV,
            requested=200,
            accepted=200,
        ),
    ]
    readiness = Mock()
    not_ready = {
        "fresh": False,
        "gate_ready": False,
        "issues": ["missing"],
        "sources": [],
        "metrics": {},
    }
    ready = {
        "fresh": True,
        "gate_ready": True,
        "issues": [],
        "sources": [SourceType.YFINANCE],
        "metrics": {},
    }
    readiness.inspect_category.side_effect = [not_ready, not_ready, ready, ready]
    service = AnalysisIngestionService(
        readiness=readiness,
        router=router,
        ingestion=ingestion,
    )

    result = service.ingest_category(str(run.id), DataCategory.OHLCV)

    preparation.refresh_from_db()
    assert result["status"] == "completed"
    assert result["sources"] == [SourceType.YFINANCE]
    assert ingestion.ingest.call_count == 2
    assert preparation.fallbacks == [
        {
            "category": DataCategory.OHLCV,
            "from": SourceType.FINNHUB,
            "to": SourceType.YFINANCE,
        }
    ]
    assert [attempt["source"] for attempt in preparation.source_attempts] == [
        SourceType.FINNHUB,
        SourceType.YFINANCE,
    ]
