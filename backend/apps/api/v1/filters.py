from __future__ import annotations

import django_filters

from apps.orchestrator.models import AnalysisRun
from apps.research.models import CatalystRecord


class AnalysisRunFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(field_name="ticker__symbol", lookup_expr="iexact")
    exchange = django_filters.CharFilter(field_name="ticker__exchange", lookup_expr="iexact")
    created_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AnalysisRun
        fields = ("status", "scope", "symbol", "exchange")


class CatalystFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(field_name="ticker__symbol", lookup_expr="iexact")
    expected_after = django_filters.IsoDateTimeFilter(field_name="expected_at", lookup_expr="gte")
    expected_before = django_filters.IsoDateTimeFilter(field_name="expected_at", lookup_expr="lte")

    class Meta:
        model = CatalystRecord
        fields = (
            "symbol",
            "catalyst_type",
            "direction",
            "outcome_status",
            "is_active",
            "is_thesis_critical",
        )
