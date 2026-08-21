from __future__ import annotations

from .models import ExitPackageStatus, ExitStrategyPackage, PMRecommendation


class PortfolioRepository:
    def active_exit_packages(self):
        return ExitStrategyPackage.objects.filter(status=ExitPackageStatus.ACTIVE).select_related(
            "analysis_run__ticker"
        )

    def approved_recommendations(self):
        return PMRecommendation.objects.filter(status="approved").select_related(
            "ticker",
            "analysis_run",
        )
