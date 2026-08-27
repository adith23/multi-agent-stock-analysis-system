import { useEffect } from "react";

import { PipelineStatus } from "@/entities/analysis";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";
import { PIPELINE_STAGES } from "../model/pipeline-stages";
import { useAnalysis } from "./use-analysis";

const TERMINAL_STATUSES = new Set([PipelineStatus.COMPLETED, PipelineStatus.FAILED, PipelineStatus.CANCELLED, PipelineStatus.BLOCKED]);

export function useAnalysisSynchronization(runId: string | null) {
  const query = useAnalysis(runId);
  useEffect(() => {
    const run = query.data;
    if (!run) return;
    if (run.status === PipelineStatus.COMPLETED) {
      usePipelineStore.getState().updateFromSSE({ type: "pipeline_completed" });
      useTerminalStore.getState().completeAnalysis();
      return;
    }
    const activeIndex = PIPELINE_STAGES.findIndex((stage) => stage.backendStatuses.includes(run.status.toUpperCase()));
    if (activeIndex >= 0) {
      PIPELINE_STAGES.forEach((stage, index) => usePipelineStore.getState().setStageStatus(stage.id, index < activeIndex ? "done" : index === activeIndex ? "running" : "pending"));
    }
    if (TERMINAL_STATUSES.has(run.status) && activeIndex >= 0) {
      usePipelineStore.getState().setStageStatus(PIPELINE_STAGES[activeIndex].id, run.status === PipelineStatus.BLOCKED ? "failed" : "done");
    }
  }, [query.data]);
  return query;
}
