import { BriefcaseBusiness, CircleCheck, Database, Gauge, ShieldCheck } from "lucide-react";

import { formatCurrency, formatNumber, formatPercentage } from "@/shared/lib";
import { isBackendRunId } from "@/shared/lib";
import { Chip, DataModeBadge, FeatureError, Meter, SectionLabel } from "@/shared/ui";
import { useTerminalStore } from "@/stores/terminal-store";

import { usePortfolio } from "../hooks/use-portfolio";
import { MOCK_PORTFOLIO_CONTEXT } from "../model/mock-portfolio-context";
import type { PortfolioContextView } from "../types/portfolio-context.types";
import { DataSourceHealth } from "./data-source-health";

export function PortfolioContextSidebar() {
  const runId = useTerminalStore((state) => state.activeRunId);
  const activeTicker = useTerminalStore((state) => state.activeTicker);
  const query = usePortfolio(undefined, isBackendRunId(runId));
  const remoteContext: PortfolioContextView | null = query.data ? {
    position: activeTicker && typeof query.data.weights[activeTicker] === "number" ? { symbol: activeTicker, portfolioCode: query.data.portfolio_code, weightPercent: Number(query.data.weights[activeTicker]) * 100, marketValue: Number(query.data.total_value) * Number(query.data.weights[activeTicker]), shares: 0 } : null,
    riskBudget: { usedPercent: typeof query.data.risk_metrics.budget_utilization === "number" ? Number(query.data.risk_metrics.budget_utilization) : 0, limitPercent: 100, remainingBps: 0 },
    mandate: { status: "within_mandate", label: query.data.name, detail: `${query.data.portfolio_code} · snapshot v${query.data.version}` },
    dataSources: MOCK_PORTFOLIO_CONTEXT.dataSources,
  } : null;
  const { position, riskBudget, mandate, dataSources } = remoteContext ?? MOCK_PORTFOLIO_CONTEXT;

  return (
    <aside className="min-h-0 w-[250px] shrink-0 overflow-y-auto border-l border-hairline bg-panel" aria-label="Portfolio context">
      <div className="px-3 pt-3">
        <SectionLabel icon={BriefcaseBusiness}>Portfolio context</SectionLabel>
        <div className="-mt-1.5 mb-3"><DataModeBadge remote={Boolean(remoteContext)} refreshing={query.isFetching} /></div>
        {query.isError ? <FeatureError className="mb-3 p-2" error={query.error} retry={() => void query.refetch()} /> : null}
      </div>

      <section className="border-t border-hairline px-3 py-3" aria-labelledby="current-position-heading">
        <h3 id="current-position-heading" className="flex items-center gap-1.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase">
          <BriefcaseBusiness className="size-3 text-blue" aria-hidden="true" />Current position
        </h3>
        {position ? (
          <dl className="mt-2 grid grid-cols-2 gap-y-1 text-[10px]">
            <dt className="text-text-faint">Weight</dt><dd className="text-right font-mono">{formatPercentage(position.weightPercent, { input: "percent" })}</dd>
            <dt className="text-text-faint">Market value</dt><dd className="text-right font-mono">{formatCurrency(position.marketValue)}</dd>
            <dt className="text-text-faint">Shares</dt><dd className="text-right font-mono">{formatNumber(position.shares)}</dd>
          </dl>
        ) : (
          <div className="mt-2 border border-dashed border-hairline-bright bg-inset/55 px-2.5 py-2">
            <strong className="block font-mono text-[12px] font-medium text-text-primary">0.0% NAV</strong>
            <span className="text-[10px] text-text-faint">No open position</span>
          </div>
        )}
      </section>

      <section className="border-t border-hairline px-3 py-3" aria-labelledby="risk-budget-heading">
        <div className="flex items-center justify-between">
          <h3 id="risk-budget-heading" className="flex items-center gap-1.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase">
            <Gauge className="size-3 text-amber" aria-hidden="true" />Risk budget
          </h3>
          <span className="font-mono text-[10px] text-text-primary">{riskBudget.usedPercent}%</span>
        </div>
        <Meter className="mt-2" value={riskBudget.usedPercent} limit={riskBudget.limitPercent} height={5} aria-label="Risk budget used" />
        <p className="mt-1.5 font-mono text-[8px] text-text-faint">{riskBudget.remainingBps} bps capacity remaining</p>
      </section>

      <section className="border-t border-hairline px-3 py-3" aria-labelledby="mandate-heading">
        <h3 id="mandate-heading" className="flex items-center gap-1.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase">
          <ShieldCheck className="size-3 text-green" aria-hidden="true" />Mandate fit
        </h3>
        <div className="mt-2 flex items-start gap-2">
          <CircleCheck className="mt-0.5 size-3.5 shrink-0 text-green" aria-hidden="true" />
          <div>
            <p className="text-[10px] font-medium text-text-primary">{mandate.label}</p>
            <p className="mt-0.5 text-[9px] leading-relaxed text-text-faint">{mandate.detail}</p>
          </div>
        </div>
      </section>

      <section className="border-y border-hairline px-3 py-3" aria-labelledby="data-sources-heading">
        <div className="flex items-center justify-between">
          <h3 id="data-sources-heading" className="flex items-center gap-1.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase">
            <Database className="size-3 text-blue" aria-hidden="true" />Data sources
          </h3>
          <Chip color="var(--color-blue)" className="min-h-4 px-1.5 py-0 text-[7px]">Mock</Chip>
        </div>
        <ul className="mt-1 divide-y divide-hairline" aria-label="Data source health">
          {dataSources.map((source) => <DataSourceHealth key={source.name} source={source} />)}
        </ul>
      </section>
    </aside>
  );
}
