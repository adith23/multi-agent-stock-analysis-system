import { describe, expect, it } from "vitest";

import { AUTH_STORAGE_KEYS, clearAuthTokens, getAccessToken, getRefreshToken, SESSION_MARKER_COOKIE, storeAccessToken, storeAuthTokens } from "@/shared/api/auth-token";

describe("auth token storage", () => {
  it("stores, rotates, and clears the browser token pair and proxy marker", () => {
    storeAuthTokens({ access: "access-1", refresh: "refresh-1" });
    expect(getAccessToken()).toBe("access-1");
    expect(getRefreshToken()).toBe("refresh-1");
    expect(document.cookie).toContain(`${SESSION_MARKER_COOKIE}=1`);

    storeAccessToken("access-2");
    expect(getAccessToken()).toBe("access-2");
    expect(window.localStorage.getItem(AUTH_STORAGE_KEYS.refresh)).toBe("refresh-1");

    clearAuthTokens();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(document.cookie).not.toContain(`${SESSION_MARKER_COOKIE}=1`);
  });
});
