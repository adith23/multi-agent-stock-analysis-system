import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { PropsWithChildren } from "react";
import { describe, expect, it, vi } from "vitest";

import type { AnalysisRun } from "@/entities/analysis";

import { pipelineApi } from "../api/pipeline.api";
import { useRunAnalysis } from "../hooks/use-run-analysis";

const completedRequest = { id: "11111111-1111-4111-8111-111111111111", symbol: "AAPL" } as AnalysisRun;

function createWrapper(retry: boolean | number = false) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry } },
  });
  return function Wrapper({ children }: PropsWithChildren) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useRunAnalysis", () => {
  it("reuses the idempotency key when a failed submission is retried by the user", async () => {
    const createAnalysis = vi.spyOn(pipelineApi, "createAnalysis")
      .mockRejectedValueOnce(new Error("request timed out"))
      .mockResolvedValueOnce(completedRequest)
      .mockResolvedValueOnce(completedRequest);
    const { result } = renderHook(() => useRunAnalysis(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({ symbol: "AAPL" }).catch(() => undefined);
    });
    await act(async () => {
      await result.current.mutateAsync({ symbol: "AAPL" });
    });

    expect(createAnalysis.mock.calls[0]?.[1]).toBe(createAnalysis.mock.calls[1]?.[1]);

    await act(async () => {
      await result.current.mutateAsync({ symbol: "AAPL" });
    });
    expect(createAnalysis.mock.calls[2]?.[1]).not.toBe(createAnalysis.mock.calls[1]?.[1]);
  });

  it("reuses the idempotency key during React Query's automatic retry", async () => {
    const createAnalysis = vi.spyOn(pipelineApi, "createAnalysis")
      .mockRejectedValueOnce(new Error("transient failure"))
      .mockResolvedValueOnce(completedRequest);
    const { result } = renderHook(() => useRunAnalysis(), { wrapper: createWrapper(1) });

    await act(async () => {
      await result.current.mutateAsync({ symbol: "AAPL", config: { horizon: "long" } });
    });

    expect(createAnalysis).toHaveBeenCalledTimes(2);
    expect(createAnalysis.mock.calls[0]?.[1]).toBe(createAnalysis.mock.calls[1]?.[1]);
  });

  it("creates a new key when the failed request is changed", async () => {
    const createAnalysis = vi.spyOn(pipelineApi, "createAnalysis")
      .mockRejectedValueOnce(new Error("request timed out"))
      .mockResolvedValueOnce({ ...completedRequest, symbol: "MSFT" });
    const { result } = renderHook(() => useRunAnalysis(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({ symbol: "AAPL" }).catch(() => undefined);
    });
    await act(async () => {
      await result.current.mutateAsync({ symbol: "MSFT" });
    });

    expect(createAnalysis.mock.calls[0]?.[1]).not.toBe(createAnalysis.mock.calls[1]?.[1]);
  });
});
