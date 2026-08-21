from celery import shared_task

from .services import (
    CatalystMonitorService,
    ExitMonitorService,
    PerformanceService,
    PMReviewService,
)


@shared_task(name="apps.portfolio.tasks.monitor_exit_triggers")
def monitor_exit_triggers() -> dict[str, int]:
    return ExitMonitorService().monitor()


@shared_task(name="apps.portfolio.tasks.monitor_catalysts")
def monitor_catalysts() -> dict[str, int]:
    return CatalystMonitorService().monitor()


@shared_task(name="apps.portfolio.tasks.track_recommendation_performance")
def track_recommendation_performance() -> dict[str, int]:
    return PerformanceService().track_due()


@shared_task(name="apps.portfolio.tasks.expire_pm_reviews")
def expire_pm_reviews() -> dict[str, int]:
    return {"expired": PMReviewService().expire_due()}
