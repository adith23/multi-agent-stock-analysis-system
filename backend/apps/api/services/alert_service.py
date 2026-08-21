from __future__ import annotations

from django.utils import timezone

from apps.portfolio.models import ExitPackageStatus, ExitStrategyPackage
from apps.research.models import CatalystRecord
from apps.signals.models import RegimeTransitionAlert


class AlertService:
    """Read-only aggregation boundary for heterogeneous active alerts."""

    @staticmethod
    def active(*, severity: str | None = None) -> list[dict]:
        alerts = [
            *AlertService._regime_alerts(severity=severity),
            *AlertService._exit_alerts(severity=severity),
            *AlertService._catalyst_alerts(severity=severity),
        ]
        return sorted(alerts, key=lambda item: item["detected_at"], reverse=True)

    @staticmethod
    def _regime_alerts(*, severity: str | None) -> list[dict]:
        queryset = RegimeTransitionAlert.objects.filter(
            acknowledged_at__isnull=True,
        ).select_related("current_state", "previous_state")
        if severity:
            queryset = queryset.filter(severity=severity)
        return [
            {
                "id": str(alert.id),
                "type": "regime_transition",
                "severity": alert.severity,
                "detected_at": alert.detected_at,
                "symbol": None,
                "title": "Market regime transition",
                "details": {
                    "from": alert.previous_state.regime if alert.previous_state else None,
                    "to": alert.current_state.regime,
                    "rationale": alert.rationale,
                },
            }
            for alert in queryset
        ]

    @staticmethod
    def _exit_alerts(*, severity: str | None) -> list[dict]:
        if severity and severity != "critical":
            return []
        queryset = ExitStrategyPackage.objects.filter(
            status=ExitPackageStatus.TRIGGERED,
        ).select_related("analysis_run__ticker")
        return [
            {
                "id": str(package.id),
                "type": "exit_trigger",
                "severity": "critical",
                "detected_at": package.triggered_at or package.updated_at,
                "symbol": package.analysis_run.ticker.symbol,
                "title": f"Exit trigger: {package.trigger_type}",
                "details": package.trigger_details,
            }
            for package in queryset
        ]

    @staticmethod
    def _catalyst_alerts(*, severity: str | None) -> list[dict]:
        if severity and severity not in {"warning", "critical"}:
            return []
        queryset = CatalystRecord.objects.filter(
            is_active=True,
            alert_sent=True,
            outcome_status="delayed",
        ).select_related("ticker")
        return [
            {
                "id": str(catalyst.id),
                "type": "catalyst_delayed",
                "severity": "critical" if catalyst.is_thesis_critical else "warning",
                "detected_at": catalyst.last_checked_at or timezone.now(),
                "symbol": catalyst.ticker.symbol,
                "title": catalyst.title,
                "details": {
                    "expected_at": catalyst.expected_at,
                    "outcome_status": catalyst.outcome_status,
                    "impact": catalyst.impact,
                },
            }
            for catalyst in queryset
            if not severity
            or severity == ("critical" if catalyst.is_thesis_critical else "warning")
        ]
