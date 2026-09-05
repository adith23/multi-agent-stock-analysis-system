import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/shared/api";

import { visualizationApi } from "../api/visualization.api";

export function usePerformance(symbol?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.performance(symbol),
    queryFn: () => visualizationApi.getPerformance(symbol),
    enabled,
  });
}
