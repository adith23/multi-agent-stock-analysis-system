import type { SpecialistReport } from "@/entities/agent";
import { apiClient, ENDPOINTS } from "@/shared/api";

export const specialistApi = {
  async getReports(runId: string): Promise<SpecialistReport[]> {
    return (await apiClient.get<SpecialistReport[]>(ENDPOINTS.ANALYSIS_SPECIALISTS(runId))).data;
  },
};
