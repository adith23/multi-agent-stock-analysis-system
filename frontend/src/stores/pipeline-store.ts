import { create } from "zustand";

export const DEFAULT_PIPELINE_STAGE_IDS = [
  "data",
  "macro",
  "fundamental",
  "technical",
  "sentiment",
  "bullbear",
  "risk",
  "compliance",
  "pm",
] as const;

export type PipelineStageStatus = "pending" | "running" | "done" | "failed" | "skipped";

/**
 * Frontend-normalized progress events. The SSE transport maps the named wire
 * events and backend stage identifiers into this stable store boundary.
 */
export type PipelineSSEEvent =
  | { type: "stage_started"; stage_id: string }
  | { type: "stage_completed"; stage_id: string }
  | { type: "stage_failed"; stage_id: string }
  | { type: "stage_skipped"; stage_id: string }
  | { type: "pipeline_completed" }
  | { type: "pipeline_failed"; stage_id?: string };

export interface PipelineState {
  stages: Record<string, PipelineStageStatus>;
  initializeStages: (stageIds: readonly string[]) => void;
  setStageStatus: (stageId: string, status: PipelineStageStatus) => void;
  resetAllStages: () => void;
  updateFromSSE: (event: PipelineSSEEvent) => void;
}

function createPendingStages(stageIds: readonly string[]): Record<string, PipelineStageStatus> {
  return Object.fromEntries(stageIds.map((stageId) => [stageId, "pending"]));
}

export const initialPipelineStages = createPendingStages(DEFAULT_PIPELINE_STAGE_IDS);

export const usePipelineStore = create<PipelineState>()((set) => ({
  stages: { ...initialPipelineStages },
  initializeStages: (stageIds) => set({ stages: createPendingStages(stageIds) }),
  setStageStatus: (stageId, status) =>
    set((state) => ({ stages: { ...state.stages, [stageId]: status } })),
  resetAllStages: () =>
    set((state) => ({ stages: createPendingStages(Object.keys(state.stages)) })),
  updateFromSSE: (event) =>
    set((state) => {
      if (event.type === "pipeline_completed") {
        return {
          stages: Object.fromEntries(
            Object.entries(state.stages).map(([stageId, status]) => [
              stageId,
              status === "failed" ? status : "done",
            ]),
          ),
        };
      }

      const stageId = event.stage_id;
      if (!stageId) return state;

      const statusByEvent = {
        stage_started: "running",
        stage_completed: "done",
        stage_failed: "failed",
        stage_skipped: "skipped",
        pipeline_failed: "failed",
      } as const;

      return {
        stages: {
          ...state.stages,
          [stageId]: statusByEvent[event.type],
        },
      };
    }),
}));
