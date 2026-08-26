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
 * Frontend-normalized progress events. The backend does not expose a WebSocket
 * consumer yet; its future transport adapter must map the agreed wire format
 * into this stable store boundary.
 */
export type PipelineWebSocketEvent =
  | { type: "pipeline.stage_started"; stage_id: string }
  | { type: "pipeline.stage_completed"; stage_id: string }
  | { type: "pipeline.stage_failed"; stage_id: string }
  | { type: "pipeline.stage_skipped"; stage_id: string }
  | { type: "pipeline.completed" }
  | { type: "pipeline.failed"; stage_id?: string };

export interface PipelineState {
  stages: Record<string, PipelineStageStatus>;
  initializeStages: (stageIds: readonly string[]) => void;
  setStageStatus: (stageId: string, status: PipelineStageStatus) => void;
  resetAllStages: () => void;
  updateFromWebSocket: (event: PipelineWebSocketEvent) => void;
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
  updateFromWebSocket: (event) =>
    set((state) => {
      if (event.type === "pipeline.completed") {
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
        "pipeline.stage_started": "running",
        "pipeline.stage_completed": "done",
        "pipeline.stage_failed": "failed",
        "pipeline.stage_skipped": "skipped",
        "pipeline.failed": "failed",
      } as const;

      return {
        stages: {
          ...state.stages,
          [stageId]: statusByEvent[event.type],
        },
      };
    }),
}));
