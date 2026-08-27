"use client";

import { useEffect, useState } from "react";

import { AUTH_TOKEN_CHANGED_EVENT, getAccessToken } from "@/shared/api/auth-token";
import { buildAuthenticatedSseUrl } from "@/shared/api/sse";

export function useAuthenticatedSseUrl(path: string, enabled: boolean): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    function synchronizeUrl() {
      const token = getAccessToken();
      setUrl(enabled && token ? buildAuthenticatedSseUrl(path, token) : null);
    }

    synchronizeUrl();
    window.addEventListener(AUTH_TOKEN_CHANGED_EVENT, synchronizeUrl);
    window.addEventListener("storage", synchronizeUrl);
    return () => {
      window.removeEventListener(AUTH_TOKEN_CHANGED_EVENT, synchronizeUrl);
      window.removeEventListener("storage", synchronizeUrl);
    };
  }, [enabled, path]);

  return url;
}
