import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  MOCK_STAGE_RUNNING_MS,
  PIPELINE_STAGES,
  usePipelineAnimation,
} from "@/features/analysis-pipeline";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useTerminalStore } from "@/stores/terminal-store";

describe("usePipelineAnimation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    usePipelineStore.getState().resetAllStages();
    useTerminalStore.getState().resetTerminal();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("drives the pending-running-done lifecycle and completes the terminal", () => {
    const { result } = renderHook(() => usePipelineAnimation());

    act(() => result.current.startMockAnalysis(" aapl "));
    expect(useTerminalStore.getState()).toMatchObject({ activeTicker: "AAPL", systemState: "running" });

    act(() => vi.advanceTimersByTime(0));
    expect(usePipelineStore.getState().stages.data).toBe("running");

    act(() => vi.advanceTimersByTime(MOCK_STAGE_RUNNING_MS));
    expect(usePipelineStore.getState().stages.data).toBe("done");

    act(() => vi.runAllTimers());
    expect(PIPELINE_STAGES.every((stage) => usePipelineStore.getState().stages[stage.id] === "done")).toBe(true);
    expect(useTerminalStore.getState().systemState).toBe("ready");
  });

  it("cancels timers and clears transient run state", () => {
    const { result } = renderHook(() => usePipelineAnimation());
    act(() => result.current.startMockAnalysis("MSFT"));
    act(() => result.current.cancelMockAnalysis());

    expect(useTerminalStore.getState()).toMatchObject({ activeRunId: null, systemState: "idle" });
    expect(Object.values(usePipelineStore.getState().stages).every((status) => status === "pending")).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
  });
});
