import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/shared/api";
import { isBackendRunId } from "@/shared/lib";

import { recommendationApi } from "../api/recommendation.api";

export function useRecommendation(runId: string | null) {
  return useQuery({
    queryKey: queryKeys.analysis.recommendation(runId ?? "inactive"),
    queryFn: () => recommendationApi.getRecommendation(runId as string),
    enabled: isBackendRunId(runId),
  });
}

export function useConviction(runId: string | null) {
  return useQuery({
    queryKey: queryKeys.analysis.conviction(runId ?? "inactive"),
    queryFn: () => recommendationApi.getConviction(runId as string),
    enabled: isBackendRunId(runId),
  });
}
