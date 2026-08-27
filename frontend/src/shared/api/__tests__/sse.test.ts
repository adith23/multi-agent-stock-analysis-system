import { describe, expect, it } from "vitest";

import { buildAuthenticatedSseUrl, parseSseJson, SSE_ENDPOINTS } from "@/shared/api";

describe("SSE API utilities", () => {
  it("builds encoded stream URLs with authentication and resume parameters", () => {
    const path = SSE_ENDPOINTS.PIPELINE_PROGRESS("run/id");
    const url = new URL(buildAuthenticatedSseUrl(path, "short-lived-token", "evt 42"));

    expect(url.pathname).toBe("/api/v1/analysis/run%2Fid/stream/");
    expect(url.searchParams.get("token")).toBe("short-lived-token");
    expect(url.searchParams.get("last_event_id")).toBe("evt 42");
  });

  it("accepts JSON objects and rejects malformed or primitive event payloads", () => {
    expect(parseSseJson<{ stage: string }>(new MessageEvent("stage_started", { data: '{"stage":"ingesting"}' }))).toEqual({ stage: "ingesting" });
    expect(parseSseJson(new MessageEvent("message", { data: "not-json" }))).toBeNull();
    expect(parseSseJson(new MessageEvent("message", { data: "42" }))).toBeNull();
  });
});
