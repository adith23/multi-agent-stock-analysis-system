import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { AnalysisScope, PipelineStatus } from "@/entities/analysis";
import { authApi } from "@/features/auth/api/auth.api";
import { publicEnvironment } from "@/shared/config/public-env";
import { mockApiServer } from "@/test/msw/server";

import { pipelineApi } from "../api/pipeline.api";

describe("API integration contracts", () => {
  it("maps authentication responses through the shared Axios client", async () => {
    await expect(authApi.login({ username: "pm.test", password: "correct-horse" })).resolves.toEqual({
      access: "test-access",
      refresh: "test-refresh",
    });
    await expect(authApi.me()).resolves.toMatchObject({ username: "pm.test", role: "portfolio_manager" });
  });

  it("sends analysis payloads and the required idempotency header", async () => {
    mockApiServer.use(http.post(`${publicEnvironment.apiBaseUrl}/analysis/`, async ({ request }) => {
      expect(request.headers.get("Idempotency-Key")).toBe("analysis-test-key");
      expect(await request.json()).toEqual({ symbol: "AAPL" });
      return HttpResponse.json({
        id: "11111111-1111-4111-8111-111111111111",
        created_at: "2026-08-27T00:00:00Z",
        updated_at: "2026-08-27T00:00:00Z",
        symbol: "AAPL",
        exchange: "NASDAQ",
        scope: AnalysisScope.SINGLE,
        status: PipelineStatus.PENDING,
        current_stage: "",
        initiated_by: "user-1",
        celery_task_id: "",
        data_cutoff_at: "2026-08-27T00:00:00Z",
        configuration_hash: "hash",
        manifest_hash: "",
        error_message: "",
        started_at: null,
        completed_at: null,
        steps: [],
      });
    }));

    await expect(pipelineApi.createAnalysis({ symbol: "AAPL" }, "analysis-test-key")).resolves.toMatchObject({
      symbol: "AAPL",
      status: PipelineStatus.PENDING,
    });
  });

  it("normalizes backend failures for feature-level retry handling", async () => {
    mockApiServer.use(http.post(`${publicEnvironment.apiBaseUrl}/analysis/`, () => HttpResponse.json(
      { detail: "The requested symbol is not supported." },
      { status: 422 },
    )));

    await expect(pipelineApi.createAnalysis({ symbol: "BAD" }, "analysis-error-key")).rejects.toMatchObject({
      status: 422,
      message: "The requested symbol is not supported.",
    });
  });
});
