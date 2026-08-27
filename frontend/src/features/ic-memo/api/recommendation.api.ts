import type { ConvictionResponse, PMRecommendation, PMReviewRequest, PMReviewResponse } from "@/entities/recommendation";
import { apiClient, ENDPOINTS } from "@/shared/api";

export const recommendationApi = {
  async getRecommendation(runId: string): Promise<PMRecommendation> {
    return (await apiClient.get<PMRecommendation>(ENDPOINTS.ANALYSIS_RECOMMENDATION(runId))).data;
  },
  async getConviction(runId: string): Promise<ConvictionResponse> {
    return (await apiClient.get<ConvictionResponse>(ENDPOINTS.ANALYSIS_CONVICTION(runId))).data;
  },
  async submitReview(runId: string, request: PMReviewRequest, idempotencyKey: string): Promise<PMReviewResponse> {
    return (await apiClient.post<PMReviewResponse>(ENDPOINTS.ANALYSIS_REVIEW(runId), request, {
      headers: { "Idempotency-Key": idempotencyKey },
    })).data;
  },
};
