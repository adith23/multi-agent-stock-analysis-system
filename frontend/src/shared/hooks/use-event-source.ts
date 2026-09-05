"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { SseConnectionStatus } from "@/shared/api/sse";

export interface UseEventSourceOptions {
  onMessage: (event: MessageEvent<string>) => void;
  onError?: (event: Event) => void;
  onOpen?: (event: Event) => void;
  eventTypes?: readonly string[];
  withCredentials?: boolean;
  lastEventId?: string | null;
}

export interface EventSourceState {
  status: SseConnectionStatus;
  lastEventId: string | null;
  close: () => void;
}

export function useEventSource(url: string | null, options: UseEventSourceOptions): EventSourceState {
  const sourceRef = useRef<EventSource | null>(null);
  const callbacksRef = useRef(options);
  const lastEventIdRef = useRef(options.lastEventId ?? null);
  const [connection, setConnection] = useState<{ url: string; status: SseConnectionStatus } | null>(null);
  const [lastEventId, setLastEventId] = useState<string | null>(options.lastEventId ?? null);
  const status: SseConnectionStatus = !url ? "idle" : connection?.url === url ? connection.status : "connecting";

  const eventTypesKey = useMemo(() => JSON.stringify([...new Set(options.eventTypes ?? [])].sort()), [options.eventTypes]);

  useEffect(() => {
    callbacksRef.current = options;
  }, [options]);

  const close = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    if (url) setConnection({ url, status: "closed" });
  }, [url]);

  useEffect(() => {
    if (!url) {
      sourceRef.current?.close();
      sourceRef.current = null;
      return;
    }

    const connectionUrl = appendLastEventId(url, lastEventIdRef.current);
    const source = new EventSource(connectionUrl, { withCredentials: options.withCredentials ?? true });
    sourceRef.current = source;

    const handleMessage = (event: Event) => {
      const message = event as MessageEvent<string>;
      if (message.lastEventId) {
        lastEventIdRef.current = message.lastEventId;
        setLastEventId(message.lastEventId);
      }
      callbacksRef.current.onMessage(message);
    };

    const eventTypes = (JSON.parse(eventTypesKey) as string[]).filter((eventType) => eventType !== "message");
    source.addEventListener("message", handleMessage);
    eventTypes.forEach((eventType) => source.addEventListener(eventType, handleMessage));
    source.onopen = (event) => {
      setConnection({ url, status: "open" });
      callbacksRef.current.onOpen?.(event);
    };
    source.onerror = (event) => {
      const reconnecting = source.readyState === EventSource.CONNECTING;
      setConnection({ url, status: reconnecting ? "reconnecting" : "error" });
      callbacksRef.current.onError?.(event);
    };

    return () => {
      eventTypes.forEach((eventType) => source.removeEventListener(eventType, handleMessage));
      source.removeEventListener("message", handleMessage);
      source.close();
      if (sourceRef.current === source) sourceRef.current = null;
    };
  }, [eventTypesKey, options.withCredentials, url]);

  return { status, lastEventId, close };
}

function appendLastEventId(url: string, lastEventId: string | null): string {
  if (!lastEventId) return url;
  const parsed = new URL(url);
  parsed.searchParams.set("last_event_id", lastEventId);
  return parsed.toString();
}
