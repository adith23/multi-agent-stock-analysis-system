import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { storeAccessToken, storeAuthTokens } from "@/shared/api/auth-token";
import { useAuthenticatedSseUrl } from "@/shared/hooks/use-authenticated-sse-url";

describe("useAuthenticatedSseUrl", () => {
  it("creates and rotates authenticated URLs without exposing a stale access token", async () => {
    const { result, rerender } = renderHook(
      ({ enabled }) => useAuthenticatedSseUrl("/alerts/stream/", enabled),
      { initialProps: { enabled: true } },
    );
    expect(result.current).toBeNull();

    act(() => storeAuthTokens({ access: "access-1", refresh: "refresh" }));
    await waitFor(() => expect(new URL(result.current as string).searchParams.get("token")).toBe("access-1"));

    act(() => storeAccessToken("access-2"));
    await waitFor(() => expect(new URL(result.current as string).searchParams.get("token")).toBe("access-2"));

    rerender({ enabled: false });
    await waitFor(() => expect(result.current).toBeNull());
  });
});
