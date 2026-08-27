"use client";

import dynamic from "next/dynamic";

function ChartLoader() {
  return <div className="h-64 animate-pulse rounded-terminal bg-inset" role="status" aria-label="Loading chart" />;
}

export const LazyPriceChart = dynamic(() => import("./price-chart").then((module) => module.PriceChart), { ssr: false, loading: ChartLoader });
export const LazyAllocationPieChart = dynamic(() => import("./allocation-pie-chart").then((module) => module.AllocationPieChart), { ssr: false, loading: ChartLoader });
export const LazyRiskWaterfallChart = dynamic(() => import("./risk-waterfall-chart").then((module) => module.RiskWaterfallChart), { ssr: false, loading: ChartLoader });
export const LazyPerformanceBarChart = dynamic(() => import("./performance-bar-chart").then((module) => module.PerformanceBarChart), { ssr: false, loading: ChartLoader });
