"""Read repository for versioned research artifacts."""

from __future__ import annotations

from typing import Any

from apps.research.models import BullBearDecisionMemo, SpecialistReport


class ResearchRepository:
    def specialist_reports_for_run(self, analysis_run_id: str) -> list[dict[str, Any]]:
        return list(
            SpecialistReport.objects.filter(analysis_run_id=analysis_run_id)
            .order_by("specialist_type", "-version")
            .values(
                "specialist_type",
                "thesis",
                "summary",
                "evidence",
                "assumptions",
                "limitations",
                "confidence",
                "version",
            )
        )

    def recent_specialist_reports(
        self,
        ticker: str,
        specialist_type: str,
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return list(
            SpecialistReport.objects.filter(
                ticker__symbol=ticker.upper(),
                specialist_type=specialist_type,
            )
            .order_by("-generated_at")
            .values(
                "thesis",
                "summary",
                "confidence",
                "evidence",
                "assumptions",
                "limitations",
                "generated_at",
                "version",
            )[:limit]
        )

    def recent_decision_memos(self, ticker: str, *, limit: int = 5) -> list[dict[str, Any]]:
        return list(
            BullBearDecisionMemo.objects.filter(ticker__symbol=ticker.upper())
            .order_by("-created_at")
            .values(
                "bull_case",
                "bear_case",
                "base_case",
                "key_disagreements",
                "falsifiers",
                "evidence",
                "confidence",
                "created_at",
                "version",
            )[:limit]
        )
