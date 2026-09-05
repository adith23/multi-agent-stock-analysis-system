import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserRole, type User } from "@/entities/user";
import { usePipelineStream } from "@/features/analysis-pipeline/hooks/use-pipeline-stream";
import { useAlertStream } from "@/features/alert-stream";
import { clearAuthTokens, storeAuthTokens } from "@/shared/api";
import { useAuditStore, useAuthStore, usePipelineStore, useTerminalStore } from "@/stores";

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }));

class EventSourceMock extends EventTarget {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;
  static instances: EventSourceMock[] = [];
  readonly url: string;
  readonly withCredentials: boolean;
  readyState = EventSourceMock.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(url: string | URL, init?: EventSourceInit) {
    super();
    this.url = String(url);
    this.withCredentials = init?.withCredentials ?? false;
    EventSourceMock.instances.push(this);
  }

  close() {
    this.readyState = EventSourceMock.CLOSED;
  }
}

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
    vi.stubGlobal("EventSource", EventSourceMock);
    EventSourceMock.instances = [];
    clearAuthTokens();
    useAuthStore.getState().setAuthenticated(user);
    storeAuthTokens({ access: "stream-access", refresh: "refresh" });
    usePipelineStore.getState().resetAllStages();
    useTerminalStore.getState().resetTerminal();
    useAuditStore.getState().clearEntries();
  });

  it("updates pipeline stages and invalidates analysis queries on terminal events", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    useTerminalStore.getState().startAnalysis("HLXD", runId);
    const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    renderHook(() => usePipelineStream(runId), { wrapper });

    await waitFor(() => expect(EventSourceMock.instances).toHaveLength(1));
    const source = EventSourceMock.instances[0];
    expect(new URL(source.url).pathname).toBe(`/api/v1/analysis/${runId}/stream/`);

    act(() => source.dispatchEvent(new MessageEvent("stage_started", { data: '{"stage":"ingesting","timestamp":"2026-08-27T10:00:00Z"}', lastEventId: "evt-1" })));
    expect(usePipelineStore.getState().stages.data).toBe("running");

    act(() => source.dispatchEvent(new MessageEvent("pipeline_completed", { data: `{"run_id":"${runId}","timestamp":"2026-08-27T10:01:00Z"}`, lastEventId: "evt-2" })));
    expect(useTerminalStore.getState().systemState).toBe("ready");
    expect(Object.values(usePipelineStore.getState().stages)).toEqual(expect.arrayContaining(["done"]));
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["analysis"] });
  });

  it("turns alert events into toasts, audit entries, and alert-cache invalidation", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidate = vi.spyOn(queryClient, "invalidateQueries");
    const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    renderHook(() => useAlertStream(), { wrapper });

    await waitFor(() => expect(EventSourceMock.instances).toHaveLength(1));
    const source = EventSourceMock.instances[0];
    act(() => source.dispatchEvent(new MessageEvent("regime_change", { data: '{"regime":"risk_off","previous":"risk_on","detected_at":"2026-08-27T10:02:00Z"}' })));
    act(() => source.dispatchEvent(new MessageEvent("exit_trigger", { data: '{"ticker":"HLXD","trigger":"stop_loss","price":198.5}' })));

    expect(useAuditStore.getState().entries).toHaveLength(2);
    expect(useAuditStore.getState().entries[0].summary).toContain("HLXD exit trigger");
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["alerts"] });
  });
});
