import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { AnalysisCreateRequest } from "@/entities/analysis";
import { normalizeApiError, queryKeys } from "@/shared/api";
import { createIdempotencyKey } from "@/shared/lib";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";

import { pipelineApi } from "../api/pipeline.api";

export function useRunAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: [...queryKeys.analysis.all, "create"],
    mutationFn: (request: AnalysisCreateRequest) =>
      pipelineApi.createAnalysis(request, createIdempotencyKey(`analysis:${request.symbol}`)),
    onSuccess: (run) => {
      queryClient.setQueryData(queryKeys.analysis.detail(run.id), run);
      usePipelineStore.getState().resetAllStages();
      useTerminalStore.getState().startAnalysis(run.symbol, run.id);
      toast.success(`Analysis queued for ${run.symbol}`);
    },
    onError: (error) => {
      useTerminalStore.getState().failAnalysis();
      toast.error("Analysis could not be started", { description: normalizeApiError(error).message });
    },
  });
}
