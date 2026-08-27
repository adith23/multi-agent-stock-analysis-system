export const AUTH_STORAGE_KEYS = {
  access: "conclave_access_token",
  legacyAccess: "auth_token",
  refresh: "conclave_refresh_token",
} as const;

/** Non-sensitive navigation hint for Next.js Proxy; never an authorization credential. */
export const SESSION_MARKER_COOKIE = "conclave_session";

export interface StoredAuthTokens {
  access: string;
  refresh: string;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(AUTH_STORAGE_KEYS.access) ?? window.localStorage.getItem(AUTH_STORAGE_KEYS.legacyAccess);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(AUTH_STORAGE_KEYS.refresh);
}

export function storeAuthTokens(tokens: StoredAuthTokens): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_STORAGE_KEYS.access, tokens.access);
  window.localStorage.setItem(AUTH_STORAGE_KEYS.refresh, tokens.refresh);
  window.localStorage.removeItem(AUTH_STORAGE_KEYS.legacyAccess);
  setSessionMarker();
}

export function storeAccessToken(access: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_STORAGE_KEYS.access, access);
  setSessionMarker();
}

export function clearAuthTokens(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_STORAGE_KEYS.access);
  window.localStorage.removeItem(AUTH_STORAGE_KEYS.refresh);
  window.localStorage.removeItem(AUTH_STORAGE_KEYS.legacyAccess);
  document.cookie = `${SESSION_MARKER_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

function setSessionMarker(): void {
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${SESSION_MARKER_COOKIE}=1; Path=/; Max-Age=604800; SameSite=Lax${secure}`;
}
