import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useEventSource } from "@/shared/hooks/use-event-source";

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
  close = vi.fn(() => { this.readyState = EventSourceMock.CLOSED; });

  constructor(url: string | URL, init?: EventSourceInit) {
    super();
    this.url = String(url);
    this.withCredentials = init?.withCredentials ?? false;
    EventSourceMock.instances.push(this);
  }

  open() {
    this.readyState = EventSourceMock.OPEN;
    this.onopen?.(new Event("open"));
  }

  fail(reconnecting: boolean) {
    this.readyState = reconnecting ? EventSourceMock.CONNECTING : EventSourceMock.CLOSED;
    this.onerror?.(new Event("error"));
  }
}

describe("useEventSource", () => {
  beforeEach(() => {
    EventSourceMock.instances = [];
    vi.stubGlobal("EventSource", EventSourceMock);
  });

  it("tracks native connection/reconnection state, named events, resume IDs, and cleanup", () => {
    const onMessage = vi.fn();
    const { result, rerender, unmount } = renderHook(
      ({ url }) => useEventSource(url, { onMessage, eventTypes: ["stage_started"], withCredentials: true }),
      { initialProps: { url: "https://api.example/stream?token=redacted" as string | null } },
    );
    const first = EventSourceMock.instances[0];
    expect(result.current.status).toBe("connecting");
    expect(first.withCredentials).toBe(true);

    act(() => first.open());
    expect(result.current.status).toBe("open");

    act(() => first.dispatchEvent(new MessageEvent("stage_started", { data: '{"stage":"data"}', lastEventId: "evt-7" })));
    expect(onMessage).toHaveBeenCalledOnce();
    expect(result.current.lastEventId).toBe("evt-7");

    act(() => first.fail(true));
    expect(result.current.status).toBe("reconnecting");

    rerender({ url: "https://api.example/stream?token=rotated" });
    const second = EventSourceMock.instances[1];
    expect(first.close).toHaveBeenCalled();
    expect(new URL(second.url).searchParams.get("last_event_id")).toBe("evt-7");

    unmount();
    expect(second.close).toHaveBeenCalled();
  });

  it("does not connect while the URL is disabled and supports an explicit close", () => {
    const { result, rerender } = renderHook(
      ({ url }) => useEventSource(url, { onMessage: vi.fn() }),
      { initialProps: { url: null as string | null } },
    );
    expect(result.current.status).toBe("idle");
    expect(EventSourceMock.instances).toHaveLength(0);

    rerender({ url: "https://api.example/stream" });
    act(() => result.current.close());
    expect(result.current.status).toBe("closed");
    expect(EventSourceMock.instances[0].close).toHaveBeenCalled();
  });
});
