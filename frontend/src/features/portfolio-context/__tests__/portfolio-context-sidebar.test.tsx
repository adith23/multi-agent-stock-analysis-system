import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PortfolioContextSidebar } from "@/features/portfolio-context";

describe("PortfolioContextSidebar", () => {
  it("renders portfolio, mandate, risk, and source-health fixtures transparently", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><PortfolioContextSidebar /></QueryClientProvider>);

    expect(screen.getByRole("complementary", { name: "Portfolio context" })).toBeVisible();
    expect(screen.getByText("Typed fixture")).toBeVisible();
    expect(screen.getByText("No open position")).toBeVisible();
    expect(screen.getByRole("progressbar", { name: "Risk budget used" })).toHaveAttribute("aria-valuenow", "41");
    expect(screen.getByText("Within style box")).toBeVisible();
    expect(screen.getByText("SEC EDGAR")).toBeVisible();
  });
});
