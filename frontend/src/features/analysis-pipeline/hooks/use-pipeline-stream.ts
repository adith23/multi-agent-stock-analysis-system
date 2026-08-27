"use client";

import { useCallback, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { PipelineSseEventType, PipelineStageEventData, PipelineTerminalEventData } from "@/entities/analysis";
import { parseSseJson, queryKeys, SSE_ENDPOINTS } from "@/shared/api";
import { useAuthenticatedSseUrl, useEventSource } from "@/shared/hooks";
import { isBackendRunId } from "@/shared/lib";
import { usePipelineStore, useTerminalStore } from "@/stores";

import { PIPELINE_SSE_EVENT_TYPES, resolvePipelineStageIds } from "../model/pipeline-sse";

export function usePipelineStream(runId: string | null) {
  const queryClient = useQueryClient();
  const systemState = useTerminalStore((state) => state.systemState);
  const enabled = isBackendRunId(runId) && systemState === "running";
  const path = SSE_ENDPOINTS.PIPELINE_PROGRESS(runId ?? "inactive");
  const url = useAuthenticatedSseUrl(path, enabled);
  const closeRef = useRef<() => void>(() => undefined);

  const onMessage = useCallback((event: MessageEvent<string>) => {
    const eventType = event.type as PipelineSseEventType;
    if (eventType === "pipeline_completed") {
      const payload = parseSseJson<PipelineTerminalEventData>(event);
      if (!payload || payload.run_id !== runId) return;
      usePipelineStore.getState().updateFromSSE({ type: eventType });
      useTerminalStore.getState().completeAnalysis();
      void queryClient.invalidateQueries({ queryKey: queryKeys.analysis.all });
      toast.success("Analysis pipeline completed");
      closeRef.current();
      return;
    }

    if (eventType === "pipeline_failed") {
      const payload = parseSseJson<PipelineTerminalEventData>(event);
      if (!payload || payload.run_id !== runId) return;
      const stageIds = payload.stage ? resolvePipelineStageIds(payload.stage) : [];
      stageIds.forEach((stageId) => usePipelineStore.getState().updateFromSSE({ type: eventType, stage_id: stageId }));
      useTerminalStore.getState().failAnalysis();
      void queryClient.invalidateQueries({ queryKey: queryKeys.analysis.all });
      toast.error("Analysis pipeline failed", { description: payload.error || "The backend did not provide an error detail." });
      closeRef.current();
      return;
    }

    const payload = parseSseJson<PipelineStageEventData>(event);
    if (!payload?.stage) return;
    resolvePipelineStageIds(payload.stage).forEach((stageId) => {
      usePipelineStore.getState().updateFromSSE({ type: eventType, stage_id: stageId });
    });
  }, [queryClient, runId]);

  const stream = useEventSource(url, { onMessage, eventTypes: PIPELINE_SSE_EVENT_TYPES, withCredentials: true });
  useEffect(() => {
    closeRef.current = stream.close;
  }, [stream.close]);
  return stream;
}
