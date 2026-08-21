from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.market_data.models import OHLCVBar, Ticker
from apps.signals.models import TechnicalSignal
from apps.signals.services import SignalExtractionService


@pytest.mark.django_db
def test_signal_extraction_service_reads_canonical_data_and_persists_signal() -> None:
    ticker = Ticker.objects.create(symbol="AAPL", exchange="US")
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = []
    for index in range(60):
        price = Decimal("100") + Decimal(index) / 2
        bars.append(
            OHLCVBar(
                ticker=ticker,
                timestamp=start + timedelta(days=index),
                interval="1d",
                open=price,
                high=price + 2,
                low=price - 1,
                close=price + 1,
                volume=Decimal(1_000_000 + index * 1000),
                source_type="fixture",
                source_id=str(index),
                source_timestamp=start + timedelta(days=index),
                data_quality_score=1,
                content_hash=f"{index:064x}",
            )
        )
    OHLCVBar.objects.bulk_create(bars)

    result = SignalExtractionService().extract_technical(ticker)

    signal = TechnicalSignal.objects.get()
    assert result["technical_signal_id"] == str(signal.id)
    assert signal.signal_type == "composite_technical"
    assert signal.source_type == "deterministic_engine"
    assert signal.direction == "bullish"
