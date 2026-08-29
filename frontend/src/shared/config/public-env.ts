const FALLBACK_API_BASE_URL = "http://localhost:8000/api/v1";

function parseHttpUrl(name: string, value: string): string {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`${name} must be an absolute HTTP(S) URL.`);
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error(`${name} must use the http or https protocol.`);
  }

  return value.replace(/\/$/, "");
}

export interface PublicEnvironment {
  apiBaseUrl: string;
  sseBaseUrl: string;
}

export function parsePublicEnvironment(apiBaseUrl?: string, sseBaseUrl?: string): Readonly<PublicEnvironment> {
  const api = apiBaseUrl || FALLBACK_API_BASE_URL;
  return Object.freeze({
    apiBaseUrl: parseHttpUrl("NEXT_PUBLIC_API_BASE_URL", api),
    sseBaseUrl: parseHttpUrl("NEXT_PUBLIC_SSE_BASE_URL", sseBaseUrl || api),
  });
}

export const publicEnvironment = parsePublicEnvironment(
  process.env.NEXT_PUBLIC_API_BASE_URL,
  process.env.NEXT_PUBLIC_SSE_BASE_URL,
);

export function assertProductionPublicEnvironment(
  environment: Readonly<PublicEnvironment> = publicEnvironment,
  nodeEnvironment = process.env.NODE_ENV,
): void {
  if (nodeEnvironment !== "production") return;

  for (const [name, value] of Object.entries(environment)) {
    const url = new URL(value);
    if (url.username || url.password) throw new Error(`${name} must not contain embedded credentials.`);
  }
}
