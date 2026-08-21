from django.contrib import admin

from .models import (
    ExitStrategyPackage,
    IdeaRanking,
    PerformanceAttributionRecord,
    PMRecommendation,
    PMReviewRequest,
    PortfolioConstructionOutput,
    PositionSizingRecommendation,
    ScenarioAnalysisResult,
)

admin.site.register(
    (
        ExitStrategyPackage,
        IdeaRanking,
        PMRecommendation,
        PMReviewRequest,
        PerformanceAttributionRecord,
        PortfolioConstructionOutput,
        PositionSizingRecommendation,
        ScenarioAnalysisResult,
    )
)
