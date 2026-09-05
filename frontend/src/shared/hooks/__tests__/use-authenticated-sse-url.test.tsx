import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { clearAuthTokens, storeAccessToken, storeAuthTokens } from "@/shared/api/auth-token";
import { useAuthenticatedSseUrl } from "@/shared/hooks/use-authenticated-sse-url";

describe("useAuthenticatedSseUrl", () => {
  beforeEach(() => {
    clearAuthTokens();
  });

  it("creates clean authenticated stream URLs when authenticated and null when unauthenticated or disabled", async () => {
    const { result, rerender } = renderHook(
      ({ enabled }) => useAuthenticatedSseUrl("/alerts/stream/", enabled),
      { initialProps: { enabled: true } },
    );
    expect(result.current).toBeNull();

    act(() => storeAuthTokens({ access: "access-1", refresh: "refresh" }));
    await waitFor(() => {
      expect(result.current).not.toBeNull();
      const url = new URL(result.current as string);
      expect(url.pathname).toBe("/api/v1/alerts/stream/");
      // Ensures JWT is NOT leaked into the URL query string
      expect(url.searchParams.has("token")).toBe(false);
    });

    act(() => storeAccessToken("access-2"));
    await waitFor(() => {
      expect(result.current).not.toBeNull();
      const url = new URL(result.current as string);
      expect(url.pathname).toBe("/api/v1/alerts/stream/");
      expect(url.searchParams.has("token")).toBe(false);
    });

    rerender({ enabled: false });
    await waitFor(() => expect(result.current).toBeNull());

    rerender({ enabled: true });
    await waitFor(() => expect(result.current).not.toBeNull());

    act(() => clearAuthTokens());
    await waitFor(() => expect(result.current).toBeNull());
  });
});
