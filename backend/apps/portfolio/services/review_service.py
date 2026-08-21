from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.core.domain.enums import PipelineStatus

from ..exceptions import ReviewConflictError, ReviewExpiredError, ReviewSubmissionError
from ..models import (
    PMRecommendation,
    PMReviewRequest,
    RecommendationStatus,
    ReviewRequestStatus,
)


@dataclass(frozen=True, slots=True)
class ReviewSubmission:
    request: PMReviewRequest
    replayed: bool


class PMReviewService:
    @transaction.atomic
    def submit(
        self,
        *,
        recommendation_id,
        decision: str,
        rationale: str,
        reviewer,
        expected_version: int,
        idempotency_key: str,
    ) -> ReviewSubmission:
        recommendation = (
            PMRecommendation.objects.select_for_update()
            .select_related("analysis_run")
            .get(pk=recommendation_id)
        )
        try:
            review = PMReviewRequest.objects.select_for_update().get(recommendation=recommendation)
        except PMReviewRequest.DoesNotExist:
            review = PMReviewRequest.objects.create(
                recommendation=recommendation,
                checkpoint_thread_id=(f"{recommendation.analysis_run.checkpoint_thread_id}-pm"),
                expires_at=timezone.now() + timedelta(hours=settings.PM_REVIEW_TTL_HOURS),
            )
        if review.idempotency_key == idempotency_key:
            if review.decision != decision or review.rationale != rationale:
                raise ReviewConflictError(
                    "The idempotency key was already used for a different review payload."
                )
            return ReviewSubmission(review, replayed=True)
        if (
            PMReviewRequest.objects.filter(idempotency_key=idempotency_key)
            .exclude(pk=review.pk)
            .exists()
        ):
            raise ReviewConflictError("The idempotency key was already used.")
        if review.is_expired:
            review.status = ReviewRequestStatus.EXPIRED
            review.save(update_fields=("status", "updated_at"))
            raise ReviewExpiredError("The PM review request has expired.")
        if review.status != ReviewRequestStatus.PENDING:
            raise ReviewConflictError("The recommendation has already been reviewed.")
        if review.lock_version != expected_version:
            raise ReviewConflictError(
                f"Review version conflict; current version is {review.lock_version}."
            )
        run = recommendation.analysis_run
        if run.status != PipelineStatus.AWAITING_PM_APPROVAL:
            raise ReviewSubmissionError("The analysis is not awaiting PM approval.")
        gate = run.analysis_config.get("approval_gate", {})
        if decision == "approve" and gate.get("decision") in {"block", "escalate"}:
            raise ReviewSubmissionError(
                "Approval is prohibited until the binding risk or compliance gate is cleared."
            )

        now = timezone.now()
        review.status = ReviewRequestStatus.COMPLETED
        review.decision = decision
        review.decided_by = reviewer
        review.rationale = rationale
        review.decided_at = now
        review.idempotency_key = idempotency_key
        review.lock_version += 1
        review.save(
            update_fields=(
                "status",
                "decision",
                "decided_by",
                "rationale",
                "decided_at",
                "idempotency_key",
                "lock_version",
                "updated_at",
            )
        )
        recommendation.status = {
            "approve": RecommendationStatus.APPROVED,
            "reject": RecommendationStatus.REJECTED,
            "defer": RecommendationStatus.DEFERRED,
        }[decision]
        recommendation.reviewer = reviewer
        recommendation.review_rationale = rationale
        recommendation.reviewed_at = now
        recommendation.save(
            update_fields=(
                "status",
                "reviewer",
                "review_rationale",
                "reviewed_at",
                "updated_at",
            )
        )
        AuditService.record_event(
            action=AuditAction.UPDATE,
            event_type="analysis.pm_review_requested",
            actor=reviewer,
            resource_type="PMReviewRequest",
            resource_id=str(review.id),
            summary=f"PM review submitted: {decision}",
            metadata={
                "analysis_run_id": str(run.id),
                "decision": decision,
                "review_version": review.lock_version,
            },
        )
        transaction.on_commit(
            lambda: self._resume(
                run_id=str(run.id),
                decision=decision,
                rationale=rationale,
                reviewer_id=str(reviewer.id),
            )
        )
        return ReviewSubmission(review, replayed=False)

    @staticmethod
    def _resume(*, run_id: str, decision: str, rationale: str, reviewer_id: str) -> None:
        from apps.orchestrator.tasks import resume_pm_decision

        resume_pm_decision.delay(
            run_id,
            decision=decision,
            rationale=rationale,
            reviewer_id=reviewer_id,
        )

    @transaction.atomic
    def expire_due(self) -> int:
        now = timezone.now()
        reviews = (
            PMReviewRequest.objects.select_for_update()
            .select_related("recommendation__analysis_run")
            .filter(status=ReviewRequestStatus.PENDING, expires_at__lte=now)
        )
        expired = 0
        for review in reviews:
            review.status = ReviewRequestStatus.EXPIRED
            review.save(update_fields=("status", "updated_at"))
            run = review.recommendation.analysis_run
            if run.status == PipelineStatus.AWAITING_PM_APPROVAL:
                run.transition_to(PipelineStatus.CANCELLED)
            expired += 1
        return expired
