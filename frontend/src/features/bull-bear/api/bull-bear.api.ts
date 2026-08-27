import type { BullBearDecisionMemo } from "@/entities/agent";
import { apiClient, ENDPOINTS } from "@/shared/api";

export const bullBearApi = {
  async getMemo(runId: string): Promise<BullBearDecisionMemo> {
    return (await apiClient.get<BullBearDecisionMemo>(ENDPOINTS.ANALYSIS_BULL_BEAR(runId))).data;
  },
};
