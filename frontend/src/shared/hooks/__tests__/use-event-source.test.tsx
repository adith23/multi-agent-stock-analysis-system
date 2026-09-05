import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { clearAuthTokens, storeAuthTokens } from "@/shared/api/auth-token";
import type { FetchEventSourceInit, ServerSentEvent } from "@/shared/api/fetch-event-source";
import { useEventSource } from "@/shared/hooks/use-event-source";

interface MockStream {
  url: string;
  options: FetchEventSourceInit;
  open: () => void;
  emit: (event: ServerSentEvent) => void;
  fail: (err?: unknown) => void;
}

let mockStreams: MockStream[] = [];

vi.mock("@/shared/api/fetch-event-source", () => ({
  fetchEventSource: vi.fn(async (url: string, options: FetchEventSourceInit) => {
    let closed = false;
    const stream: MockStream = {
      url,
      options,
      open: () => {
        options.onopen?.(new Response(null, { status: 200, headers: { "content-type": "text/event-stream" } }));
      },
      emit: (event: ServerSentEvent) => {
        options.onmessage?.(event);
      },
      fail: (err?: unknown) => {
        options.onerror?.(err || new Error("Stream connection failed"));
      },
    };
    mockStreams.push(stream);

    return new Promise<void>((resolve) => {
      options.signal?.addEventListener("abort", () => {
        if (!closed) {
          closed = true;
          options.onclose?.();
          resolve();
        }
      });
    });
  }),
}));

describe("useEventSource", () => {
  beforeEach(() => {
    mockStreams = [];
    clearAuthTokens();
    storeAuthTokens({ access: "test-access-token", refresh: "test-refresh-token" });
  });

  it("tracks connection/reconnection state, named events, resume IDs, Bearer headers, and cleanup", async () => {
    const onMessage = vi.fn();
    const { result, rerender, unmount } = renderHook(
      ({ url }) =>
        useEventSource(url, {
          onMessage,
          eventTypes: ["stage_started"],
          lastEventId: "evt-initial",
        }),
      { initialProps: { url: "https://api.example/stream" as string | null } },
    );

    await waitFor(() => expect(mockStreams).toHaveLength(1));
    const first = mockStreams[0];
    expect(result.current.status).toBe("connecting");

    // Verify Authorization Bearer header and Last-Event-ID are passed
    expect(first.options.headers?.Authorization).toBe("Bearer test-access-token");
    expect(first.options.headers?.["Last-Event-ID"]).toBe("evt-initial");

    act(() => first.open());
    expect(result.current.status).toBe("open");

    // Emit event matching eventTypes filter
    act(() => first.emit({ id: "evt-7", event: "stage_started", data: '{"stage":"data"}' }));
    expect(onMessage).toHaveBeenCalledOnce();
    expect(result.current.lastEventId).toBe("evt-7");

    // Test reconnection state on error
    act(() => first.fail());
    expect(result.current.status).toBe("reconnecting");

    // Rerender with new URL rotates the stream
    rerender({ url: "https://api.example/stream-v2" });
    await waitFor(() => expect(mockStreams).toHaveLength(2));
    const second = mockStreams[1];
    expect(first.options.signal?.aborted).toBe(true);
    expect(second.options.headers?.["Last-Event-ID"]).toBe("evt-7");

    unmount();
    expect(second.options.signal?.aborted).toBe(true);
  });

  it("does not connect while URL is disabled and supports explicit close", async () => {
    const onMessage = vi.fn();
    const { result, rerender } = renderHook(
      ({ url }) => useEventSource(url, { onMessage }),
      { initialProps: { url: null as string | null } },
    );
    expect(result.current.status).toBe("idle");
    expect(mockStreams).toHaveLength(0);

    rerender({ url: "https://api.example/stream" });
    await waitFor(() => expect(mockStreams).toHaveLength(1));
    expect(result.current.status).toBe("connecting");

    act(() => result.current.close());
    expect(result.current.status).toBe("closed");
    expect(mockStreams[0].options.signal?.aborted).toBe(true);
  });
});
