from __future__ import annotations

from django.db import transaction

from .models import AnalysisRun


class AnalysisRunRepository:
    def get(self, run_id: str) -> AnalysisRun:
        return AnalysisRun.objects.select_related("ticker", "initiated_by").get(pk=run_id)

    @transaction.atomic
    def get_for_update(self, run_id: str) -> AnalysisRun:
        return (
            AnalysisRun.objects.select_for_update()
            .select_related("ticker", "initiated_by")
            .get(pk=run_id)
        )
