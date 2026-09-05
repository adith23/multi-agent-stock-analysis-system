import { publicEnvironment } from "@/shared/config/public-env";

export type SseConnectionStatus =
  | "idle"
  | "connecting"
  | "open"
  | "reconnecting"
  | "closed"
  | "error";

export function buildSseUrl(path: string, lastEventId?: string | null): string {
  const configuredBase = publicEnvironment.sseBaseUrl;
  const url = new URL(`${configuredBase}/${path.replace(/^\//, "")}`);
  if (lastEventId) {
    url.searchParams.set("last_event_id", lastEventId);
  }
  return url.toString();
}

/**
 * Clean URL builder without JWT in query parameters.
 * Authorization tokens are transmitted securely via HTTP Authorization Bearer headers.
 */
export function buildAuthenticatedSseUrl(
  path: string,
  _accessToken?: string,
  lastEventId?: string | null,
): string {
  return buildSseUrl(path, lastEventId);
}

export function parseSseJson<T>(
  event: { data: string } | MessageEvent<string>,
): T | null {
  try {
    const value: unknown = JSON.parse(event.data);
    return value && typeof value === "object" && !Array.isArray(value)
      ? (value as T)
      : null;
  } catch {
    return null;
  }
}
