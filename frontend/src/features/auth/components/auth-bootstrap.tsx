"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { clearAuthTokens, getAccessToken } from "@/shared/api";
import { useAuthStore } from "@/stores";

import { authApi } from "../api/auth.api";

export function AuthBootstrap({ children }: Readonly<{ children: ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const status = useAuthStore((state) => state.status);
  const setAuthenticated = useAuthStore((state) => state.setAuthenticated);
  const setUnauthenticated = useAuthStore((state) => state.setUnauthenticated);

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!getAccessToken()) {
        clearAuthTokens();
        if (active) setUnauthenticated();
        if (pathname !== "/login") router.replace("/login");
        return;
      }
      try {
        const user = await authApi.me();
        if (active) setAuthenticated(user);
      } catch {
        clearAuthTokens();
        if (active) setUnauthenticated();
        if (pathname !== "/login") router.replace("/login");
      }
    }

    function handleUnauthorized() {
      clearAuthTokens();
      setUnauthenticated();
      if (pathname !== "/login") router.replace("/login");
    }

    void bootstrap();
    window.addEventListener("conclave:unauthorized", handleUnauthorized);
    return () => {
      active = false;
      window.removeEventListener("conclave:unauthorized", handleUnauthorized);
    };
  }, [pathname, router, setAuthenticated, setUnauthenticated]);

  if (pathname !== "/login" && status !== "authenticated") {
    return <div className="terminal-workspace-grid grid min-h-dvh place-items-center bg-void font-mono text-[10px] tracking-[0.14em] text-text-faint uppercase" role="status">Verifying secure session…</div>;
  }
  return children;
}
