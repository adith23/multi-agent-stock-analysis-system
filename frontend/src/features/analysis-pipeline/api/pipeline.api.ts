import type { AnalysisCreateRequest, AnalysisRun, PipelineStatus } from "@/entities/analysis";
import { apiClient, ENDPOINTS } from "@/shared/api";
import type { PaginatedResponse } from "@/shared/types";

export interface AnalysisListParams {
  page?: number;
  page_size?: number;
  symbol?: string;
  exchange?: string;
  status?: PipelineStatus;
  search?: string;
  ordering?: string;
}

export const pipelineApi = {
  async createAnalysis(request: AnalysisCreateRequest, idempotencyKey: string): Promise<AnalysisRun> {
    const response = await apiClient.post<AnalysisRun>(ENDPOINTS.ANALYSIS_LIST, request, {
      headers: { "Idempotency-Key": idempotencyKey },
    });
    return response.data;
  },
  async getAnalysis(runId: string): Promise<AnalysisRun> {
    return (await apiClient.get<AnalysisRun>(ENDPOINTS.ANALYSIS_DETAIL(runId))).data;
  },
  async listAnalyses(params: AnalysisListParams = {}): Promise<PaginatedResponse<AnalysisRun>> {
    return (await apiClient.get<PaginatedResponse<AnalysisRun>>(ENDPOINTS.ANALYSIS_LIST, { params })).data;
  },
};
