import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/shared/api";
import { isBackendRunId } from "@/shared/lib";

import { pipelineApi } from "../api/pipeline.api";

export function useAnalysis(runId: string | null) {
  return useQuery({
    queryKey: queryKeys.analysis.detail(runId ?? "inactive"),
    queryFn: () => pipelineApi.getAnalysis(runId as string),
    enabled: isBackendRunId(runId),
  });
}
