from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.market_data.models import OHLCVBar

from ..models import ExitPackageStatus
from ..repositories import PortfolioRepository


class ExitMonitorService:
    def __init__(self, repository: PortfolioRepository | None = None) -> None:
        self.repository = repository or PortfolioRepository()

    @transaction.atomic
    def monitor(self) -> dict[str, int]:
        checked = triggered = 0
        now = timezone.now()
        for package in self.repository.active_exit_packages().select_for_update():
            latest = (
                OHLCVBar.objects.filter(ticker=package.analysis_run.ticker)
                .order_by("-timestamp")
                .first()
            )
            if latest is None:
                continue
            checked += 1
            price = Decimal(latest.close)
            trigger_type = ""
            if price <= package.stop_loss_price:
                trigger_type = "stop_loss"
            else:
                reached = [
                    target
                    for target in package.profit_targets
                    if price >= Decimal(str(target["price"]))
                ]
                if reached:
                    trigger_type = "profit_target"
                elif now >= package.time_based_review_date:
                    trigger_type = "time_review"
            package.current_price = price
            package.last_checked_at = now
            fields = ["current_price", "last_checked_at", "updated_at"]
            if trigger_type:
                triggered += 1
                package.status = ExitPackageStatus.TRIGGERED
                package.trigger_type = trigger_type
                package.triggered_at = now
                package.trigger_details = {"price": str(price)}
                fields.extend(("status", "trigger_type", "triggered_at", "trigger_details"))
                AuditService.record_event(
                    action=AuditAction.UPDATE,
                    event_type="portfolio.exit_triggered",
                    resource_type="ExitStrategyPackage",
                    resource_id=str(package.id),
                    summary=f"{trigger_type} triggered at {price}",
                )
            package.save(update_fields=fields)
        return {"checked": checked, "triggered": triggered}
