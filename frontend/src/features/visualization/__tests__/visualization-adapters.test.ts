import { describe, expect, it } from "vitest";

import type { PerformanceResponse, PortfolioRisk, PortfolioState } from "@/entities/portfolio";
import { toAllocationData, toPerformanceData, toRiskWaterfallData, unwrapPerformanceResponse } from "@/features/visualization/model/visualization-adapters";

describe("visualization adapters", () => {
  it("normalizes portfolio weights and risk metrics into chart-safe percentages", () => {
    const portfolio = { sector_exposures: { technology: 0.6, healthcare: 0.4 }, weights: {} } as unknown as PortfolioState;
    const risk = { risk_metrics: { market_risk: 0.22, hedge: -0.05, nested: { ignored: true } } } as unknown as PortfolioRisk;

    expect(toAllocationData(portfolio)).toEqual([{ name: "Technology", value: 60 }, { name: "Healthcare", value: 40 }]);
    expect(toRiskWaterfallData(risk)).toEqual([{ name: "Market Risk", impact: 22 }, { name: "Hedge", impact: -5 }]);
  });

  it("supports the backend paginated performance envelope", () => {
    const payload = { summary: { hit_rate: 1 }, records: [{ symbol: "AAPL", measurement_period: "1m", realized_return: 0.08, benchmark_return: 0.05, excess_return: 0.03 }] } as unknown as PerformanceResponse;

    expect(unwrapPerformanceResponse({ results: payload as never })).toBe(payload);
    expect(toPerformanceData(payload)).toEqual([{ label: "AAPL 1m", portfolio: 8, benchmark: 5, excess: 3 }]);
  });
});
