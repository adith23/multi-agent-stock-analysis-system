export const AUTH_STORAGE_KEYS = {
  access: "conclave_access_token",
  legacyAccess: "auth_token",
  refresh: "conclave_refresh_token",
} as const;

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(AUTH_STORAGE_KEYS.access) ?? window.localStorage.getItem(AUTH_STORAGE_KEYS.legacyAccess);
}
