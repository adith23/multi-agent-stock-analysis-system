import { NextResponse, type NextRequest } from "next/server";

import { SESSION_MARKER_COOKIE } from "@/shared/api/auth-token";

export function proxy(request: NextRequest) {
  // This is an optimistic navigation check only. Django validates every Bearer
  // token and role; the client bootstrap rejects stale or forged markers.
  const hasSessionMarker = request.cookies.get(SESSION_MARKER_COOKIE)?.value === "1";
  const isLogin = request.nextUrl.pathname === "/login";

  if (!hasSessionMarker && !isLogin) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }
  if (hasSessionMarker && isLogin) return NextResponse.redirect(new URL("/", request.url));
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
