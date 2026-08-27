function fallbackId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

export function createIdempotencyKey(scope: string): string {
  const safeScope = scope.toLowerCase().replace(/[^a-z0-9._:-]+/g, "-").slice(0, 48) || "request";
  const id = globalThis.crypto?.randomUUID?.() ?? fallbackId();
  return `${safeScope}:${id}`.slice(0, 128);
}

export function isBackendRunId(runId: string | null | undefined): runId is string {
  return Boolean(runId && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(runId));
}
