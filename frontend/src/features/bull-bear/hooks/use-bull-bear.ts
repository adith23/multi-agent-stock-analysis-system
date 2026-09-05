import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api";
import { isBackendRunId } from "@/shared/lib";
import { bullBearApi } from "../api/bull-bear.api";

export function useBullBear(runId: string | null) {
  return useQuery({ queryKey: queryKeys.analysis.bullBear(runId ?? "inactive"), queryFn: () => bullBearApi.getMemo(runId as string), enabled: isBackendRunId(runId) });
}
