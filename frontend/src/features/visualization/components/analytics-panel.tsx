"use client";

import { BarChart3, CandlestickChart, ChartPie, ShieldAlert } from "lucide-react";

import { canAccessSensitiveData } from "@/entities/user";
import { usePortfolio, usePortfolioRisk } from "@/features/portfolio-context";
import { DataModeBadge, Panel, SectionLabel } from "@/shared/ui";
import { useTerminalStore } from "@/stores";

import { usePerformance } from "../hooks/use-performance";
import { MOCK_ALLOCATION, MOCK_OHLCV, MOCK_PERFORMANCE, MOCK_RISK_WATERFALL } from "../model/mock-visualization";
import { toAllocationData, toPerformanceData, toRiskWaterfallData } from "../model/visualization-adapters";
import { LazyAllocationPieChart, LazyPerformanceBarChart, LazyPriceChart, LazyRiskWaterfallChart } from "./lazy-charts";

export function AnalyticsPanel() {
  const role = useTerminalStore((state) => state.role);
  const symbol = useTerminalStore((state) => state.activeTicker) ?? "AAPL";
  const canLoadPortfolio = canAccessSensitiveData(role);
  const portfolio = usePortfolio(undefined, canLoadPortfolio);
  const risk = usePortfolioRisk(undefined, canLoadPortfolio);
  const performance = usePerformance(undefined, canLoadPortfolio);

  const allocationData = portfolio.data ? toAllocationData(portfolio.data) : MOCK_ALLOCATION;
  const riskData = risk.data ? toRiskWaterfallData(risk.data) : MOCK_RISK_WATERFALL;
  const performanceData = performance.data ? toPerformanceData(performance.data) : MOCK_PERFORMANCE;

  return (
    <div className="grid w-full max-w-[1180px] grid-cols-2 gap-4">
      <Panel className="col-span-2 p-4">
        <div className="mb-3 flex items-start justify-between">
          <div><SectionLabel icon={CandlestickChart}>Interactive price history</SectionLabel><p className="text-xs text-text-dim">Candlestick and area modes with crosshair inspection.</p></div>
          <div className="text-right"><DataModeBadge remote={false} /><p className="mt-1 font-mono text-[7px] text-text-faint">PUBLIC OHLCV ENDPOINT NOT EXPOSED</p></div>
        </div>
        <LazyPriceChart data={MOCK_OHLCV} symbol={symbol} />
      </Panel>

      <ChartPanel title="Portfolio allocation" icon={ChartPie} remote={Boolean(portfolio.data)} refreshing={portfolio.isFetching} note={chartNote(portfolio.error, canLoadPortfolio)}>
        <LazyAllocationPieChart data={allocationData} />
      </ChartPanel>
      <ChartPanel title="Risk budget waterfall" icon={ShieldAlert} remote={Boolean(risk.data)} refreshing={risk.isFetching} note={chartNote(risk.error, canLoadPortfolio)}>
        <LazyRiskWaterfallChart data={riskData} />
      </ChartPanel>
      <Panel className="col-span-2 p-4">
        <div className="mb-3 flex items-start justify-between"><div><SectionLabel icon={BarChart3}>Performance attribution</SectionLabel><p className="text-xs text-text-dim">Portfolio returns compared with the recorded benchmark.</p></div><DataModeBadge remote={Boolean(performance.data)} refreshing={performance.isFetching} /></div>
        {chartNote(performance.error, canLoadPortfolio) ? <p className="mb-2 font-mono text-[8px] text-text-faint">{chartNote(performance.error, canLoadPortfolio)}</p> : null}
        <LazyPerformanceBarChart data={performanceData} />
      </Panel>
    </div>
  );
}

function ChartPanel({ title, icon, remote, refreshing, note, children }: { title: string; icon: typeof ChartPie; remote: boolean; refreshing: boolean; note: string | null; children: React.ReactNode }) {
  return <Panel className="p-4"><div className="mb-3 flex items-start justify-between"><SectionLabel icon={icon}>{title}</SectionLabel><DataModeBadge remote={remote} refreshing={refreshing} /></div>{note ? <p className="mb-2 font-mono text-[8px] text-text-faint">{note}</p> : null}{children}</Panel>;
}

function chartNote(error: unknown, permitted: boolean): string | null {
  if (!permitted) return "Your authenticated role cannot access sensitive portfolio data; showing a typed fixture.";
  if (error) return "Backend data is unavailable; showing a typed fixture.";
  return null;
}
