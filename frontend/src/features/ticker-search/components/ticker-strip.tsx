import { Activity, Database, Radio, UsersRound } from "lucide-react";

import { formatCurrency, formatPercentage } from "@/shared/lib";
import { Chip, Sparkline } from "@/shared/ui";
import { useTerminalStore } from "@/stores/terminal-store";

import { getMockQuote, MOCK_TICKER_QUOTE } from "../model/mock-ticker";

const STATE_PRESENTATION = {
  idle: { label: "Idle", color: "var(--color-text-dim)" },
  running: { label: "Analysis running", color: "var(--color-amber)" },
  ready: { label: "Analysis ready", color: "var(--color-green)" },
} as const;

export function TickerStrip() {
  const activeTicker = useTerminalStore((state) => state.activeTicker);
  const systemState = useTerminalStore((state) => state.systemState);
  const displayedSymbol = activeTicker ?? MOCK_TICKER_QUOTE.symbol;
  const quote = getMockQuote(displayedSymbol);
  const state = STATE_PRESENTATION[systemState];

  return (
    <section className="flex h-12 shrink-0 items-center justify-between gap-6 border-b border-hairline bg-inset px-3" aria-label="Selected security">
      <div className="flex min-w-0 items-center gap-3">
        <div className="shrink-0">
          <div className="flex items-baseline gap-2">
            <strong className="font-mono text-sm tracking-[0.08em] text-text-primary">{displayedSymbol}</strong>
            <span className="max-w-52 truncate text-[11px] text-text-dim">
              {quote?.companyName ?? "Awaiting market data"}
            </span>
          </div>
          <p className="mt-0.5 font-mono text-[9px] tracking-[0.1em] text-text-faint uppercase">
            {quote ? "Phase 3–4 fixture · delayed" : "Quote integration · Phase 6"}
          </p>
        </div>

        {quote ? (
          <>
            <span className="font-mono text-sm font-medium text-text-primary">
              {formatCurrency(quote.price, quote.currency)}
            </span>
            <span className="font-mono text-[11px] text-green">
              +{quote.change.toFixed(2)} · +{formatPercentage(quote.changePercent, { input: "percent" })}
            </span>
            <Sparkline points={[...quote.intradayPoints]} width={88} height={22} label={`${quote.symbol} mock intraday trend`} />
          </>
        ) : (
          <span className="font-mono text-sm text-text-faint">—</span>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-1.5">
        <Chip color="var(--color-blue)" className="gap-1"><Database className="size-3" aria-hidden="true" />Mock data</Chip>
        <Chip color="var(--color-text-dim)" className="gap-1"><UsersRound className="size-3" aria-hidden="true" />9 stages</Chip>
        <Chip color={state.color} className="gap-1" aria-live="polite">
          {systemState === "running" ? <Activity className="size-3 animate-pulse" aria-hidden="true" /> : <Radio className="size-3" aria-hidden="true" />}
          {state.label}
        </Chip>
      </div>
    </section>
  );
}
