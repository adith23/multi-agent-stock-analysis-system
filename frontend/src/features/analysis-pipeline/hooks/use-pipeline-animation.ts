import { useCallback, useEffect, useRef } from "react";

import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";

import { PIPELINE_STAGES } from "../model/pipeline-stages";

export const MOCK_STAGE_INTERVAL_MS = 420;
export const MOCK_STAGE_RUNNING_MS = 250;

function createMockRunId(ticker: string): string {
  return `mock:${ticker}:${Date.now()}`;
}

export interface PipelineAnimationController {
  startMockAnalysis: (ticker: string) => void;
  cancelMockAnalysis: () => void;
}

/** Temporary Phase 4 driver. It can be removed when the real event adapter lands. */
export function usePipelineAnimation(): PipelineAnimationController {
  const timersRef = useRef<number[]>([]);
  const runningRef = useRef(false);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current = [];
  }, []);

  const cancelMockAnalysis = useCallback(() => {
    clearTimers();
    if (runningRef.current) {
      runningRef.current = false;
      usePipelineStore.getState().resetAllStages();
      useTerminalStore.getState().failAnalysis();
    }
  }, [clearTimers]);

  const startMockAnalysis = useCallback((ticker: string) => {
    const normalizedTicker = ticker.trim().toUpperCase();
    if (!normalizedTicker) return;

    clearTimers();
    runningRef.current = true;
    usePipelineStore.getState().resetAllStages();
    useTerminalStore.getState().startAnalysis(normalizedTicker, createMockRunId(normalizedTicker));

    PIPELINE_STAGES.forEach((stage, index) => {
      const startTimer = window.setTimeout(() => {
        usePipelineStore.getState().setStageStatus(stage.id, "running");
      }, index * MOCK_STAGE_INTERVAL_MS);

      const finishTimer = window.setTimeout(() => {
        usePipelineStore.getState().setStageStatus(stage.id, "done");
        if (index === PIPELINE_STAGES.length - 1) {
          runningRef.current = false;
          useTerminalStore.getState().completeAnalysis();
        }
      }, index * MOCK_STAGE_INTERVAL_MS + MOCK_STAGE_RUNNING_MS);

      timersRef.current.push(startTimer, finishTimer);
    });
  }, [clearTimers]);

  useEffect(() => cancelMockAnalysis, [cancelMockAnalysis]);

  return { startMockAnalysis, cancelMockAnalysis };
}
