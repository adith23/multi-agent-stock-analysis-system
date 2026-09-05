import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api";
import { isBackendRunId } from "@/shared/lib";
import { specialistApi } from "../api/specialist.api";

export function useSpecialistReports(runId: string | null) {
  return useQuery({ queryKey: queryKeys.analysis.specialists(runId ?? "inactive"), queryFn: () => specialistApi.getReports(runId as string), enabled: isBackendRunId(runId) });
}
