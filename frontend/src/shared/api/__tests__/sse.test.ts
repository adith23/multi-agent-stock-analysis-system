import { describe, expect, it } from "vitest";

import { buildAuthenticatedSseUrl, buildSseUrl, parseSseJson, SSE_ENDPOINTS } from "@/shared/api";

describe("SSE API utilities", () => {
  it("builds clean stream URLs with resume parameter and without query token leakage", () => {
    const path = SSE_ENDPOINTS.PIPELINE_PROGRESS("run/id");
    const url = new URL(buildAuthenticatedSseUrl(path, "short-lived-token", "evt 42"));

    expect(url.pathname).toBe("/api/v1/analysis/run%2Fid/stream/");
    // Verify tokens are not leaked into URL query parameters
    expect(url.searchParams.has("token")).toBe(false);
    expect(url.searchParams.get("last_event_id")).toBe("evt 42");

    const cleanUrl = new URL(buildSseUrl(path, "evt 42"));
    expect(cleanUrl.pathname).toBe("/api/v1/analysis/run%2Fid/stream/");
    expect(cleanUrl.searchParams.has("token")).toBe(false);
    expect(cleanUrl.searchParams.get("last_event_id")).toBe("evt 42");
  });

  it("accepts JSON objects and rejects malformed or primitive event payloads", () => {
    expect(
      parseSseJson<{ stage: string }>(
        new MessageEvent("stage_started", { data: '{"stage":"ingesting"}' }),
      ),
    ).toEqual({ stage: "ingesting" });
    expect(parseSseJson(new MessageEvent("message", { data: "not-json" }))).toBeNull();
    expect(parseSseJson(new MessageEvent("message", { data: "42" }))).toBeNull();
  });
});
