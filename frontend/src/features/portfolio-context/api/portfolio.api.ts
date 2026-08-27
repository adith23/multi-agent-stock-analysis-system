import type { PortfolioRisk, PortfolioState } from "@/entities/portfolio";
import { apiClient, ENDPOINTS } from "@/shared/api";

export const portfolioApi = {
  async getState(portfolioCode?: string): Promise<PortfolioState> {
    return (await apiClient.get<PortfolioState>(ENDPOINTS.PORTFOLIO, { params: portfolioCode ? { portfolio_code: portfolioCode } : undefined })).data;
  },
  async getRisk(portfolioCode?: string): Promise<PortfolioRisk> {
    return (await apiClient.get<PortfolioRisk>(ENDPOINTS.PORTFOLIO_RISK, { params: portfolioCode ? { portfolio_code: portfolioCode } : undefined })).data;
  },
};
