import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { DEFAULT_API_BASE_URL } from "@/shared/lib/constants";

import { normalizeApiError } from "./api-error";
import { clearAuthTokens, getAccessToken, getRefreshToken, storeAccessToken, storeAuthTokens } from "./auth-token";
import { ENDPOINTS } from "./endpoints";

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  __conclaveRetryCount?: number;
  __conclaveAuthRetry?: boolean;
}

const RETRYABLE_METHODS = new Set(["get", "head", "options"]);
const MAX_TRANSPORT_RETRIES = 2;
let refreshPromise: Promise<string> | null = null;

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json", Accept: "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const normalized = normalizeApiError(error);
    const config = error.config as RetryableRequestConfig | undefined;
    const method = config?.method?.toLowerCase();
    const retryCount = config?.__conclaveRetryCount ?? 0;

    if (normalized.status === 401 && config && !config.__conclaveAuthRetry && !isAuthRequest(config.url)) {
      const refresh = getRefreshToken();
      if (refresh) {
        config.__conclaveAuthRetry = true;
        try {
          const access = await refreshAccessToken(refresh);
          config.headers.Authorization = `Bearer ${access}`;
          return apiClient(config);
        } catch {
          clearAuthTokens();
          dispatchUnauthorized();
          return Promise.reject(normalized);
        }
      }
    }

    if (config && method && RETRYABLE_METHODS.has(method) && normalized.retryable && retryCount < MAX_TRANSPORT_RETRIES) {
      config.__conclaveRetryCount = retryCount + 1;
      await new Promise((resolve) => globalThis.setTimeout(resolve, 250 * 2 ** retryCount));
      return apiClient(config);
    }

    if (normalized.status === 401) dispatchUnauthorized();
    return Promise.reject(normalized);
  },
);

function isAuthRequest(url?: string): boolean {
  return Boolean(url && [ENDPOINTS.AUTH_TOKEN, ENDPOINTS.AUTH_REFRESH, ENDPOINTS.AUTH_VERIFY].some((path) => url.includes(path)));
}

function dispatchUnauthorized(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("conclave:unauthorized"));
}

function refreshAccessToken(refresh: string): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access: string; refresh?: string }>(
        `${apiClient.defaults.baseURL}${ENDPOINTS.AUTH_REFRESH}`,
        { refresh },
        { timeout: apiClient.defaults.timeout },
      )
      .then(({ data }) => {
        if (data.refresh) storeAuthTokens({ access: data.access, refresh: data.refresh });
        else storeAccessToken(data.access);
        return data.access;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}
