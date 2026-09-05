import axios from "axios";

import type { ApiFieldErrors, JsonValue } from "@/shared/types";

export class ApiError extends Error {
  readonly status: number | null;
  readonly code: string;
  readonly fields: ApiFieldErrors;
  readonly retryable: boolean;

  constructor(options: {
    message: string;
    status?: number | null;
    code?: string;
    fields?: ApiFieldErrors;
    retryable?: boolean;
  }) {
    super(options.message);
    this.name = "ApiError";
    this.status = options.status ?? null;
    this.code = options.code ?? "api_error";
    this.fields = options.fields ?? {};
    this.retryable = options.retryable ?? false;
  }
}

function isFieldErrors(value: unknown): value is ApiFieldErrors {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function firstMessage(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstMessage(item);
      if (message) return message;
    }
  }
  if (value && typeof value === "object") {
    for (const item of Object.values(value)) {
      const message = firstMessage(item);
      if (message) return message;
    }
  }
  return null;
}

export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (!axios.isAxiosError(error)) {
    return new ApiError({ message: error instanceof Error ? error.message : "An unexpected error occurred." });
  }

  const status = error.response?.status ?? null;
  const data = error.response?.data as Record<string, JsonValue> | undefined;
  const fields = isFieldErrors(data?.errors) ? data.errors : isFieldErrors(data) ? data : {};
  const message = firstMessage(data?.detail) ?? firstMessage(data?.errors) ?? firstMessage(data) ?? error.message ?? "The API request failed.";
  const code = typeof data?.code === "string" ? data.code : status ? `http_${status}` : "network_error";
  const retryable = status === null || status === 408 || status === 429 || status >= 500;

  return new ApiError({ message, status, code, fields, retryable });
}
