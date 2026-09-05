import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserRole, type User } from "@/entities/user";
import { usePipelineStream } from "@/features/analysis-pipeline/hooks/use-pipeline-stream";
import { useAlertStream } from "@/features/alert-stream";
import type {
  FetchEventSourceInit,
  ServerSentEvent,
} from "@/shared/api/fetch-event-source";
import { clearAuthTokens, storeAuthTokens } from "@/shared/api";
import {
  useAuditStore,
  useAuthStore,
  usePipelineStore,
  useTerminalStore,
} from "@/stores";

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}));

interface ActiveStream {
  url: string;
  options: FetchEventSourceInit;
  emit: (event: ServerSentEvent) => void;
}

let activeStreams: ActiveStream[] = [];

vi.mock("@/shared/api/fetch-event-source", () => ({
  fetchEventSource: vi.fn(
    async (url: string, options: FetchEventSourceInit) => {
      const stream: ActiveStream = {
        url,
        options,
        emit: (event: ServerSentEvent) => {
          options.onmessage?.(event);
        },
      };
      activeStreams.push(stream);
      options.onopen?.(
        new Response(null, {
          status: 200,
          headers: { "content-type": "text/event-stream" },
        }),
      );

      // Keep stream alive until aborted
      return new Promise<void>((resolve) => {
        options.signal?.addEventListener("abort", () => {
          options.onclose?.();
          resolve();
        });
      });
    },
  ),
}));

const runId = "f896a8ad-72a8-4284-956b-471130c04c9c";
const user: User = {
  id: "03117970-e163-411a-916e-c51244a0bdda",
  username: "analyst",
  email: "analyst@example.com",
  first_name: "Investment",
  last_name: "Analyst",
  job_title: "Analyst",
  role: UserRole.INVESTMENT_ANALYST,
};

describe("SSE feature integration", () => {
  beforeEach(() => {
    activeStreams = [];
    clearAuthTokens();
    useAuthStore.getState().setAuthenticated(user);
    storeAuthTokens({ access: "stream-access", refresh: "refresh" });
    usePipelineStore.getState().resetAllStages();
    useTerminalStore.getState().resetTerminal();
    useAuditStore.getState().clearEntries();
  });

  it("updates pipeline stages and invalidates analysis queries on terminal events with Bearer auth", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    useTerminalStore.getState().startAnalysis("HLXD", runId);
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    renderHook(() => usePipelineStream(runId), { wrapper });

    await waitFor(() => expect(activeStreams).toHaveLength(1));
    const stream = activeStreams[0];

    // Verify clean URL without token leakage in query parameters
    const parsedUrl = new URL(stream.url);
    expect(parsedUrl.pathname).toBe(`/api/v1/analysis/${runId}/stream/`);
    expect(parsedUrl.searchParams.has("token")).toBe(false);

    // Verify Authorization Bearer header is passed
    expect(stream.options.headers?.Authorization).toBe("Bearer stream-access");

    act(() => {
      stream.emit({
        id: "evt-1",
        event: "stage_started",
        data: '{"stage":"ingesting","timestamp":"2026-08-27T10:00:00Z"}',
      });
    });
    expect(usePipelineStore.getState().stages.data).toBe("running");

    act(() => {
      stream.emit({
        id: "evt-2",
        event: "pipeline_completed",
        data: `{"run_id":"${runId}","timestamp":"2026-08-27T10:01:00Z"}`,
      });
    });
    expect(useTerminalStore.getState().systemState).toBe("ready");
    expect(Object.values(usePipelineStore.getState().stages)).toEqual(
      expect.arrayContaining(["done"]),
    );
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["analysis"] });
  });

  it("turns alert events into toasts, audit entries, and alert-cache invalidation", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    renderHook(() => useAlertStream(), { wrapper });

    await waitFor(() => expect(activeStreams).toHaveLength(1));
    const stream = activeStreams[0];

    // Verify clean URL without query token
    const parsedUrl = new URL(stream.url);
    expect(parsedUrl.pathname).toBe("/api/v1/alerts/stream/");
    expect(parsedUrl.searchParams.has("token")).toBe(false);
    expect(stream.options.headers?.Authorization).toBe("Bearer stream-access");

    act(() => {
      stream.emit({
        id: "alert-1",
        event: "regime_change",
        data: '{"regime":"risk_off","previous":"risk_on","detected_at":"2026-08-27T10:02:00Z"}',
      });
    });

    act(() => {
      stream.emit({
        id: "alert-2",
        event: "exit_trigger",
        data: '{"ticker":"HLXD","trigger":"stop_loss","price":198.5}',
      });
    });

    expect(useAuditStore.getState().entries).toHaveLength(2);
    expect(useAuditStore.getState().entries[0].summary).toContain(
      "HLXD exit trigger",
    );
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["alerts"] });
  });
});
