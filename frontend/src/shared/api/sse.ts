import { publicEnvironment } from "@/shared/config/public-env";

export type SseConnectionStatus = "idle" | "connecting" | "open" | "reconnecting" | "closed" | "error";

export function buildAuthenticatedSseUrl(path: string, accessToken: string, lastEventId?: string | null): string {
  const configuredBase = publicEnvironment.sseBaseUrl;
  const url = new URL(`${configuredBase}/${path.replace(/^\//, "")}`);
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
