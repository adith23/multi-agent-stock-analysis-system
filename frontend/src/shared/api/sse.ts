import { DEFAULT_API_BASE_URL, DEFAULT_SSE_BASE_URL } from "@/shared/lib/constants";

export type SseConnectionStatus = "idle" | "connecting" | "open" | "reconnecting" | "closed" | "error";

export function buildAuthenticatedSseUrl(path: string, accessToken: string, lastEventId?: string | null): string {
  const configuredBase = process.env.NEXT_PUBLIC_SSE_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_SSE_BASE_URL;
  const base = configuredBase || DEFAULT_API_BASE_URL;
  const url = new URL(`${base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`);
  url.searchParams.set("token", accessToken);
  if (lastEventId) url.searchParams.set("last_event_id", lastEventId);
  return url.toString();
}

export function parseSseJson<T>(event: MessageEvent<string>): T | null {
  try {
    const value: unknown = JSON.parse(event.data);
    return value && typeof value === "object" && !Array.isArray(value) ? value as T : null;
  } catch {
    return null;
  }
}
