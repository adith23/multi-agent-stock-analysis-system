import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { AuditAction } from "@/entities/audit";
import { RecommendationStatus, type PMRecommendation, type PMReviewRequest } from "@/entities/recommendation";
import { normalizeApiError, queryKeys } from "@/shared/api";
import { createIdempotencyKey } from "@/shared/lib";
import { useAuditStore } from "@/stores/audit-store";

import { recommendationApi } from "../api/recommendation.api";

const STATUS_BY_DECISION = {
  approve: RecommendationStatus.APPROVED,
  reject: RecommendationStatus.REJECTED,
  defer: RecommendationStatus.DEFERRED,
} as const;

export function usePMDecision(runId: string) {
  const queryClient = useQueryClient();
  const queryKey = queryKeys.analysis.recommendation(runId);

  return useMutation({
    mutationFn: (request: PMReviewRequest) =>
      recommendationApi.submitReview(runId, request, createIdempotencyKey(`pm-review:${runId}`)),
    onMutate: async (request) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<PMRecommendation>(queryKey);
      if (previous) queryClient.setQueryData<PMRecommendation>(queryKey, { ...previous, status: STATUS_BY_DECISION[request.decision] });
      return { previous };
    },
    onError: (error, _request, context) => {
      if (context?.previous) queryClient.setQueryData(queryKey, context.previous);
      toast.error("Decision was not recorded", { description: normalizeApiError(error).message });
    },
    onSuccess: (response) => {
      useAuditStore.getState().addEntry({
        actor_label: "PORTFOLIO MANAGER",
        action: response.decision === "approve" ? AuditAction.APPROVE : response.decision === "reject" ? AuditAction.REJECT : AuditAction.UPDATE,
        summary: `PM decision recorded: ${response.decision.toUpperCase()}`,
        reference: "FR-048",
        sync_status: "synced",
      });
      toast.success("Portfolio manager decision recorded");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey });
      void queryClient.invalidateQueries({ queryKey: queryKeys.analysis.detail(runId) });
    },
  });
}
