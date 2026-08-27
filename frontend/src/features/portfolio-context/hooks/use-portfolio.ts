import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api";
import { portfolioApi } from "../api/portfolio.api";

export function usePortfolio(portfolioCode?: string, enabled = true) {
  return useQuery({ queryKey: queryKeys.portfolio.state(portfolioCode), queryFn: () => portfolioApi.getState(portfolioCode), enabled });
}

export function usePortfolioRisk(portfolioCode?: string, enabled = true) {
  return useQuery({ queryKey: queryKeys.portfolio.risk(portfolioCode), queryFn: () => portfolioApi.getRisk(portfolioCode), enabled });
}
