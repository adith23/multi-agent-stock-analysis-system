import type { DataSourceHealth } from "@/entities/portfolio";

export interface CurrentPositionView {
  symbol: string;
  portfolioCode: string;
  weightPercent: number;
  marketValue: number;
  shares: number;
}

export interface RiskBudgetView {
  usedPercent: number;
  limitPercent: number;
  remainingBps: number;
}

export interface MandateFitView {
  status: "within_mandate" | "review_required" | "outside_mandate";
  label: string;
  detail: string;
}

export interface PortfolioContextView {
  position: CurrentPositionView | null;
  riskBudget: RiskBudgetView;
  mandate: MandateFitView;
  dataSources: readonly DataSourceHealth[];
}
