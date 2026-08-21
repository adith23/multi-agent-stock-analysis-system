from celery import shared_task

from apps.market_data.models import Ticker
from apps.signals.services import SignalExtractionService


@shared_task(name="apps.signals.tasks.extract_technical_signals")
def extract_technical_signals(
    ticker_id: str,
    *,
    interval: str = "1d",
    limit: int = 252,
) -> dict:
    ticker = Ticker.objects.get(pk=ticker_id)
    return SignalExtractionService().extract_technical(
        ticker,
        interval=interval,
        limit=limit,
    )
