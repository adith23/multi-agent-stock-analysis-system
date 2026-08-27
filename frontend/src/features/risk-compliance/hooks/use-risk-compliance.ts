import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api";
import { isBackendRunId } from "@/shared/lib";
import { riskApi } from "../api/risk.api";

export function useRiskCompliance(runId: string | null) {
  return useQuery({ queryKey: queryKeys.analysis.risk(runId ?? "inactive"), queryFn: () => riskApi.getRiskCompliance(runId as string), enabled: isBackendRunId(runId) });
}
