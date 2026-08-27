import type { PipelineSseEventType } from "@/entities/analysis";

import { PIPELINE_STAGES } from "./pipeline-stages";

export const PIPELINE_SSE_EVENT_TYPES: readonly PipelineSseEventType[] = [
  "stage_started",
  "stage_completed",
  "stage_failed",
  "stage_skipped",
  "pipeline_completed",
  "pipeline_failed",
];

export function resolvePipelineStageIds(stage: string): string[] {
  const normalized = stage.trim().toUpperCase();
  if (!normalized) return [];
  const direct = PIPELINE_STAGES.find((definition) => definition.id.toUpperCase() === normalized);
  if (direct) return [direct.id];
  return PIPELINE_STAGES.filter((definition) => definition.backendStatuses.includes(normalized)).map((definition) => definition.id);
}
