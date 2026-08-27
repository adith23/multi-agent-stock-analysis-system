import type { PerformanceResponse } from "@/entities/portfolio";
import type { JsonValue } from "@/shared/types";
import { apiClient, ENDPOINTS } from "@/shared/api";

import { unwrapPerformanceResponse } from "../model/visualization-adapters";

type PerformanceApiResponse = PerformanceResponse | { results: JsonValue };

export const visualizationApi = {
  async getPerformance(symbol?: string): Promise<PerformanceResponse> {
    const response = await apiClient.get<PerformanceApiResponse>(ENDPOINTS.PERFORMANCE, {
      params: symbol ? { symbol } : undefined,
    });
    return unwrapPerformanceResponse(response.data);
  },
};
