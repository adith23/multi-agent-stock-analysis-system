import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_PIPELINE_STAGE_IDS, usePipelineStore } from "@/stores/pipeline-store";

describe("pipeline store", () => {
  beforeEach(() => {
    usePipelineStore.getState().initializeStages(DEFAULT_PIPELINE_STAGE_IDS);
  });

  it("tracks immutable stage status changes", () => {
    const previousStages = usePipelineStore.getState().stages;
    usePipelineStore.getState().setStageStatus("macro", "running");

    expect(usePipelineStore.getState().stages.macro).toBe("running");
    expect(usePipelineStore.getState().stages).not.toBe(previousStages);
  });

  it("normalizes websocket lifecycle events", () => {
    const store = usePipelineStore.getState();
    store.updateFromSSE({ type: "stage_started", stage_id: "risk" });
    store.updateFromSSE({ type: "stage_completed", stage_id: "risk" });
    store.updateFromSSE({ type: "stage_skipped", stage_id: "compliance" });

    expect(usePipelineStore.getState().stages).toMatchObject({
      risk: "done",
      compliance: "skipped",
    });
  });

  it("marks non-failed stages done when the pipeline completes", () => {
    const store = usePipelineStore.getState();
    store.setStageStatus("technical", "failed");
    store.updateFromSSE({ type: "pipeline_completed" });

    expect(usePipelineStore.getState().stages.technical).toBe("failed");
    expect(usePipelineStore.getState().stages.macro).toBe("done");
  });

  it("resets every currently known stage", () => {
    const store = usePipelineStore.getState();
    store.setStageStatus("backend-dynamic-step", "running");
    store.resetAllStages();

    expect(usePipelineStore.getState().stages["backend-dynamic-step"]).toBe("pending");
  });
});
