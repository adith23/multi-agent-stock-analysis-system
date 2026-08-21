from __future__ import annotations

from django.db.models import Q
from django.utils import timezone

from .models import ComplianceRule, PortfolioState, RestrictedSecurity, RiskLimit


class RiskComplianceRepository:
    def active_limits(self) -> dict[str, dict]:
        return {
            item.metric: {"maximum": item.maximum, "severity": item.severity}
            for item in RiskLimit.objects.filter(is_active=True)
        }

    def active_policies(self) -> list[dict]:
        return [
            {
                "id": item.code,
                "field": item.field,
                "operator": item.operator,
                "value": item.expected_value,
                "severity": item.severity,
            }
            for item in ComplianceRule.objects.filter(is_active=True).order_by("priority", "code")
        ]

    def restricted_symbols(self) -> frozenset[str]:
        now = timezone.now()
        return frozenset(
            RestrictedSecurity.objects.filter(
                is_active=True,
                effective_at__lte=now,
            )
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
            .values_list("ticker__symbol", flat=True)
        )

    def latest_portfolio(
        self,
        portfolio_code: str | None = None,
        *,
        as_of=None,
    ) -> PortfolioState | None:
        queryset = PortfolioState.objects.order_by("-as_of")
        if portfolio_code:
            queryset = queryset.filter(portfolio_code=portfolio_code)
        if as_of is not None:
            queryset = queryset.filter(as_of__lte=as_of)
        return queryset.first()
