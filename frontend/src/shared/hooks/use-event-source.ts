"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  getAccessToken,
  getRefreshToken,
  storeAccessToken,
  storeAuthTokens,
} from "@/shared/api/auth-token";
import {
  fetchEventSource,
  type ServerSentEvent,
} from "@/shared/api/fetch-event-source";
import type { SseConnectionStatus } from "@/shared/api/sse";

export interface UseEventSourceOptions {
  onMessage: (event: MessageEvent<string>) => void;
  onError?: (event: Event | unknown) => void;
  onOpen?: (event: Event | Response) => void;
  eventTypes?: readonly string[];
  withCredentials?: boolean;
  lastEventId?: string | null;
  headers?: Record<string, string>;
}

export interface EventSourceState {
  status: SseConnectionStatus;
  lastEventId: string | null;
  close: () => void;
}

export function useEventSource(
  url: string | null,
  options: UseEventSourceOptions,
): EventSourceState {
  const abortControllerRef = useRef<AbortController | null>(null);
  const callbacksRef = useRef(options);
  const lastEventIdRef = useRef(options.lastEventId ?? null);
  const [connection, setConnection] = useState<{
    url: string;
    status: SseConnectionStatus;
  } | null>(null);
  const [lastEventId, setLastEventId] = useState<string | null>(
    options.lastEventId ?? null,
  );
  const status: SseConnectionStatus = !url
    ? "idle"
    : connection?.url === url
      ? connection.status
      : "connecting";

  const eventTypesKey = useMemo(
    () => JSON.stringify([...new Set(options.eventTypes ?? [])].sort()),
    [options.eventTypes],
  );

  useEffect(() => {
    callbacksRef.current = options;
  }, [options]);

  const close = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    if (url) {
      setConnection({ url, status: "closed" });
    }
  }, [url]);

  useEffect(() => {
    if (!url) {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      return;
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    setConnection({ url, status: "connecting" });

    const allowedTypes: string[] = JSON.parse(eventTypesKey);
    const filterEventTypes = allowedTypes.length > 0;

    async function startStream() {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        ...(options.headers ?? {}),
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      if (lastEventIdRef.current) {
        headers["Last-Event-ID"] = lastEventIdRef.current;
      }

      try {
        await fetchEventSource(url as string, {
          signal: abortController.signal,
          headers,
          async onopen(response) {
            if (abortController.signal.aborted) return;
            if (response.ok) {
              setConnection({ url: url as string, status: "open" });
              callbacksRef.current.onOpen?.(response);
            } else if (response.status === 401) {
              // Token expired - attempt refresh
              const refresh = getRefreshToken();
              if (refresh) {
                try {
                  const refreshed = await attemptTokenRefresh(refresh);
                  if (refreshed) {
                    headers.Authorization = `Bearer ${refreshed}`;
                  }
                } catch {
                  // Ignore and let error handler proceed
                }
              }
            }
          },
          onmessage(event: ServerSentEvent) {
            if (abortController.signal.aborted) return;

            if (event.id) {
              lastEventIdRef.current = event.id;
              setLastEventId(event.id);
            }

            if (
              !filterEventTypes ||
              allowedTypes.includes(event.event) ||
              event.event === "message"
            ) {
              const messageEvent = new MessageEvent(event.event, {
                data: event.data,
                lastEventId: event.id,
              });
              callbacksRef.current.onMessage(messageEvent);
            }
          },
          onclose() {
            if (!abortController.signal.aborted) {
              setConnection({ url: url as string, status: "closed" });
            }
          },
          onerror(err) {
            if (!abortController.signal.aborted) {
              setConnection({ url: url as string, status: "reconnecting" });
              callbacksRef.current.onError?.(err);
            }
          },
        });
      } catch (err) {
        if (!abortController.signal.aborted) {
          setConnection({ url: url as string, status: "error" });
          callbacksRef.current.onError?.(err);
        }
      }
    }

    void startStream();

    return () => {
      abortController.abort();
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    };
  }, [eventTypesKey, options.headers, url]);

  return { status, lastEventId, close };
}

async function attemptTokenRefresh(
  refreshToken: string,
): Promise<string | null> {
  try {
    const res = await fetch("/api/v1/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { access: string; refresh?: string };
    if (data.refresh) {
      storeAuthTokens({ access: data.access, refresh: data.refresh });
    } else {
      storeAccessToken(data.access);
    }
    return data.access;
  } catch {
    return null;
  }
}
