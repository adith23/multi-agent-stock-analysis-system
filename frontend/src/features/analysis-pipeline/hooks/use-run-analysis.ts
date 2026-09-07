import { useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { AnalysisCreateRequest } from "@/entities/analysis";
import { normalizeApiError, queryKeys } from "@/shared/api";
import { createIdempotencyKey } from "@/shared/lib";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";

import { pipelineApi } from "../api/pipeline.api";

interface PendingAnalysisSubmission {
  identity: string;
  idempotencyKey: string;
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([, entry]) => entry !== undefined)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entry]) => [key, canonicalize(entry)]),
    );
  }
  return value;
}

function submissionIdentity(request: AnalysisCreateRequest): string {
  return JSON.stringify(canonicalize(request));
}

export function useRunAnalysis() {
  const queryClient = useQueryClient();
  const pendingSubmission = useRef<PendingAnalysisSubmission | null>(null);

  return useMutation({
    mutationKey: [...queryKeys.analysis.all, "create"],
    mutationFn: (request: AnalysisCreateRequest) => {
      const identity = submissionIdentity(request);
      if (pendingSubmission.current?.identity !== identity) {
        pendingSubmission.current = {
          identity,
          idempotencyKey: createIdempotencyKey(`analysis:${request.symbol}`),
        };
      }
      return pipelineApi.createAnalysis(request, pendingSubmission.current.idempotencyKey);
    },
    onSuccess: (run, request) => {
      const identity = submissionIdentity(request);
      if (pendingSubmission.current?.identity === identity) pendingSubmission.current = null;
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
