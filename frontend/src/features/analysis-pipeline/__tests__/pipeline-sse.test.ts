import { describe, expect, it } from "vitest";

import { resolvePipelineStageIds } from "@/features/analysis-pipeline/model/pipeline-sse";

describe("pipeline SSE stage mapping", () => {
  it("maps backend orchestration statuses and direct UI stage IDs", () => {
    expect(resolvePipelineStageIds("ingesting")).toEqual(["data"]);
    expect(resolvePipelineStageIds("running_specialists")).toEqual(["macro", "fundamental", "technical", "sentiment"]);
    expect(resolvePipelineStageIds("risk")).toEqual(["risk"]);
    expect(resolvePipelineStageIds("unknown_stage")).toEqual([]);
  });
});
