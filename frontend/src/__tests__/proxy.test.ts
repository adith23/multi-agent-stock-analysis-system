import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { proxy } from "@/proxy";
import { SESSION_MARKER_COOKIE } from "@/shared/api/auth-token";

describe("authentication proxy", () => {
  it("redirects protected routes to login when no session marker exists", () => {
    const response = proxy(new NextRequest("https://terminal.example/"));
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://terminal.example/login?next=%2F");
  });

  it("allows a marked session through for client-side JWT verification", () => {
    const request = new NextRequest("https://terminal.example/", { headers: { cookie: `${SESSION_MARKER_COOKIE}=1` } });
    expect(proxy(request).headers.get("x-middleware-next")).toBe("1");
  });
});
