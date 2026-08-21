from django.db import models

from apps.core.models import TimeStampedModel, VersionedMixin


class IdeaRanking(TimeStampedModel, VersionedMixin):
    analysis_run = models.ForeignKey(
        "orchestrator.AnalysisRun",
        on_delete=models.CASCADE,
        related_name="idea_rankings",
    )
    ticker = models.ForeignKey(
        "market_data.Ticker",
        on_delete=models.CASCADE,
        related_name="idea_rankings",
    )
    rank = models.PositiveIntegerField()
    score = models.FloatField()
    criteria_scores = models.JSONField(default=dict)
    rationale = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("analysis_run", "ticker", "version"),
                name="uq_idea_ranking_run_ticker_version",
            )
        ]
        ordering = ("rank",)
