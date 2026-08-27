import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { DEFAULT_API_BASE_URL } from "@/shared/lib/constants";

import { normalizeApiError } from "./api-error";
import { getAccessToken } from "./auth-token";

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  __conclaveRetryCount?: number;
}

const RETRYABLE_METHODS = new Set(["get", "head", "options"]);
const MAX_TRANSPORT_RETRIES = 2;

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

    if (config && method && RETRYABLE_METHODS.has(method) && normalized.retryable && retryCount < MAX_TRANSPORT_RETRIES) {
      config.__conclaveRetryCount = retryCount + 1;
      await new Promise((resolve) => globalThis.setTimeout(resolve, 250 * 2 ** retryCount));
      return apiClient(config);
    }

    if (normalized.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("conclave:unauthorized"));
    }
    return Promise.reject(normalized);
  },
);
