import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AnalyticsPanel } from "@/features/visualization/components/analytics-panel";
import { useTerminalStore } from "@/stores/terminal-store";

vi.mock("@/features/visualization/components/lazy-charts", () => ({
  LazyPriceChart: () => <div>price chart</div>,
  LazyAllocationPieChart: () => <div>allocation chart</div>,
  LazyRiskWaterfallChart: () => <div>risk chart</div>,
  LazyPerformanceBarChart: () => <div>performance chart</div>,
}));

describe("AnalyticsPanel", () => {
  beforeEach(() => useTerminalStore.getState().resetTerminal());

  it("renders every Phase 9 visualization with explicit data provenance", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><AnalyticsPanel /></QueryClientProvider>);

    expect(screen.getByText("Interactive price history")).toBeVisible();
    expect(screen.getByText("Portfolio allocation")).toBeVisible();
    expect(screen.getByText("Risk budget waterfall")).toBeVisible();
    expect(screen.getByText("Performance attribution")).toBeVisible();
    expect(screen.getAllByText("Typed fixture")).toHaveLength(4);
    expect(screen.getAllByText(/authenticated role cannot access sensitive portfolio data/i)).toHaveLength(3);
  });
});
