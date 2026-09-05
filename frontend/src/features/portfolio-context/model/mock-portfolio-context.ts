import type { PortfolioContextView } from "../types/portfolio-context.types";

/** Explicit Phase 4 fixture until the portfolio and source-health endpoints are integrated. */
export const MOCK_PORTFOLIO_CONTEXT: Readonly<PortfolioContextView> = {
  position: null,
  riskBudget: {
    usedPercent: 41,
    limitPercent: 100,
    remainingBps: 590,
  },
  mandate: {
    status: "within_mandate",
    label: "Within style box",
    detail: "US large-cap growth · eligible",
  },
  dataSources: [
    { name: "Market Data Feed", status: "ok", last_sync: "2026-08-26T09:41:31+05:30" },
    { name: "SEC EDGAR", status: "delayed", last_sync: "2026-08-26T09:27:04+05:30" },
    { name: "Newswire Aggregate", status: "ok", last_sync: "2026-08-26T09:41:12+05:30" },
    { name: "Portfolio System", status: "ok", last_sync: "2026-08-26T09:41:30+05:30" },
  ],
};
