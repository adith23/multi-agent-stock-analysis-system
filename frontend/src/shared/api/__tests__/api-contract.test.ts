import { describe, expect, it, vi } from "vitest";

import { pipelineApi } from "@/features/analysis-pipeline/api/pipeline.api";
import { recommendationApi } from "@/features/ic-memo/api/recommendation.api";
import { ApiError, apiClient, createQueryClient, ENDPOINTS, normalizeApiError, queryKeys } from "@/shared/api";
import { createIdempotencyKey, isBackendRunId } from "@/shared/lib";

describe("API contract infrastructure", () => {
  it("builds URL-safe endpoint paths from the verified backend map", () => {
    expect(ENDPOINTS.ANALYSIS_REVIEW("run/id")).toBe("/analysis/run%2Fid/review/");
    expect(ENDPOINTS.AUTH_TOKEN).toBe("/auth/token/");
    expect(queryKeys.analysis.risk("abc")).toEqual(["analysis", "abc", "risk"]);
  });

  it("generates valid idempotency keys and identifies backend UUIDs", () => {
    const key = createIdempotencyKey("PM Review HLXD");
    expect(key).toMatch(/^pm-review-hlxd:/);
    expect(key.length).toBeLessThanOrEqual(128);
    expect(isBackendRunId("123e4567-e89b-42d3-a456-426614174000")).toBe(true);
    expect(isBackendRunId("mock:HLXD:1")).toBe(false);
  });

  it("normalizes DRF field and transport errors", () => {
    const fieldError = normalizeApiError({ isAxiosError: true, message: "Bad request", response: { status: 400, data: { symbol: ["This field is required."] } } });
    expect(fieldError).toBeInstanceOf(ApiError);
    expect(fieldError).toMatchObject({ status: 400, message: "This field is required.", retryable: false });
    expect(normalizeApiError(new Error("offline")).message).toBe("offline");
    const existing = new ApiError({ message: "Already normalized" });
    expect(normalizeApiError(existing)).toBe(existing);
    expect(normalizeApiError("unknown")).toMatchObject({ message: "An unexpected error occurred." });

    const serviceError = normalizeApiError({
      isAxiosError: true,
      message: "Request failed",
      response: { status: 503, data: { detail: { reason: ["Upstream unavailable"] }, code: "upstream_down" } },
    });
    expect(serviceError).toMatchObject({ status: 503, message: "Upstream unavailable", code: "upstream_down", retryable: true });
    expect(normalizeApiError({ isAxiosError: true, message: "Network Error" })).toMatchObject({
      status: null,
      code: "network_error",
      retryable: true,
    });
  });

  it("sends backend-required request bodies and idempotency headers", async () => {
    const post = vi.spyOn(apiClient, "post").mockResolvedValue({ data: { id: "run-1" } });
    await pipelineApi.createAnalysis({ symbol: "HLXD" }, "analysis:key");
    expect(post).toHaveBeenCalledWith("/analysis/", { symbol: "HLXD" }, { headers: { "Idempotency-Key": "analysis:key" } });
    await recommendationApi.submitReview("run-1", { decision: "approve", rationale: "Reviewed", expected_version: 2 }, "review:key");
    expect(post).toHaveBeenLastCalledWith("/analysis/run-1/review/", { decision: "approve", rationale: "Reviewed", expected_version: 2 }, { headers: { "Idempotency-Key": "review:key" } });
  });

  it("uses freshness-aware query defaults without mutation replay", () => {
    const client = createQueryClient();
    expect(client.getDefaultOptions().queries).toMatchObject({ staleTime: 30_000, refetchOnWindowFocus: true, refetchInterval: false });
    expect(client.getDefaultOptions().mutations?.retry).toBe(false);
    const retry = client.getDefaultOptions().queries?.retry;
    expect(typeof retry).toBe("function");
    if (typeof retry === "function") {
      expect(retry(0, new Error("transient"))).toBe(true);
      expect(retry(2, new Error("transient"))).toBe(false);
      expect(retry(0, new ApiError({ message: "transport handled" }))).toBe(false);
    }
    client.clear();
  });
});
