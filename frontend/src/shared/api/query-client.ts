import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "./api-error";

function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 2) return false;
  // ApiError instances have already passed through the Axios transport retry
  // interceptor. Avoid multiplying retries across both layers.
  return !(error instanceof ApiError);
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        retry: shouldRetry,
        refetchOnWindowFocus: true,
        refetchOnReconnect: true,
        refetchInterval: false,
      },
      mutations: { retry: false },
    },
  });
}
