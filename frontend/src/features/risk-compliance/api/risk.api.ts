import type { RiskComplianceResponse } from "@/entities/risk";
import { apiClient, ENDPOINTS } from "@/shared/api";

export const riskApi = {
  async getRiskCompliance(runId: string): Promise<RiskComplianceResponse> {
    return (await apiClient.get<RiskComplianceResponse>(ENDPOINTS.ANALYSIS_RISK(runId))).data;
  },
};
