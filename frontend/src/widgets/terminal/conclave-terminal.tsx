"use client";

import { Activity, Database, ShieldCheck } from "lucide-react";

import { AgentStance } from "@/entities/agent";
import { UserRole } from "@/entities/user";
import { useClock } from "@/shared/hooks";
import { ActionButton, Chip, Meter, Panel, SectionLabel, Sparkline, StanceIcon } from "@/shared/ui";
import { Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/shadcn";
import { useTerminalStore } from "@/stores/terminal-store";

const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.PORTFOLIO_MANAGER]: "Portfolio Manager",
  [UserRole.INVESTMENT_ANALYST]: "Investment Analyst",
  [UserRole.RESEARCH_ANALYST]: "Research Analyst",
  [UserRole.RISK_OFFICER]: "Risk Officer",
  [UserRole.COMPLIANCE_REVIEWER]: "Compliance Reviewer",
  [UserRole.SYSTEM_ADMINISTRATOR]: "System Administrator",
};

export function ConclaveTerminal() {
  const clock = useClock();
  const role = useTerminalStore((state) => state.role);
  const setRole = useTerminalStore((state) => state.setRole);
  const tickerInput = useTerminalStore((state) => state.tickerInput);
  const setTickerInput = useTerminalStore((state) => state.setTickerInput);

  return (
    <main className="min-h-screen bg-void px-5 py-8 text-text-primary sm:px-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
        <header className="flex flex-col gap-4 border-b border-hairline pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="font-mono text-[10px] tracking-[0.16em] text-amber uppercase">
              Multi-agent decision support
            </p>
            <h1 className="mt-1 font-serif text-2xl font-bold tracking-[0.02em]">Conclave Terminal</h1>
            <p className="mt-1 max-w-xl text-xs leading-relaxed text-text-dim">
              The production design system, backend contract types, client stores, and shared hooks are ready for feature assembly.
            </p>
          </div>
          <div className="flex items-center gap-2 font-mono text-[10px] text-text-faint">
            <span className="size-1.5 animate-pulse-glow rounded-full bg-green" aria-hidden="true" />
            <span>FOUNDATION READY</span>
            <time suppressHydrationWarning>{clock.toLocaleTimeString("en-GB", { hour12: false })}</time>
          </div>
        </header>

        <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
          <Panel className="min-h-72">
            <SectionLabel icon={Activity}>Design system</SectionLabel>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-terminal border border-hairline bg-inset p-3">
                <p className="font-mono text-[10px] tracking-[0.08em] text-text-faint uppercase">Pipeline health</p>
                <div className="mt-3 flex items-center gap-2">
                  <Chip color="var(--color-green)">Operational</Chip>
                  <Chip color="var(--color-amber)">Awaiting API</Chip>
                </div>
                <div className="mt-5">
                  <div className="mb-1.5 flex justify-between font-mono text-[10px] text-text-dim">
                    <span>Risk budget</span>
                    <span>41%</span>
                  </div>
                  <Meter value={41} />
                </div>
              </div>

              <div className="rounded-terminal border border-hairline bg-inset p-3">
                <p className="font-mono text-[10px] tracking-[0.08em] text-text-faint uppercase">Signal vocabulary</p>
                <div className="mt-3 flex items-center gap-5 font-mono text-xs">
                  <span className="flex items-center gap-1"><StanceIcon stance={AgentStance.BULLISH} /> Bullish</span>
                  <span className="flex items-center gap-1"><StanceIcon stance={AgentStance.BEARISH} /> Bearish</span>
                  <span className="flex items-center gap-1"><StanceIcon stance={AgentStance.NEUTRAL} /> Neutral</span>
                </div>
                <Sparkline className="mt-6" points={[14, 18, 16, 23, 21, 29, 34, 31, 39]} width={220} height={38} />
              </div>
            </div>
          </Panel>

          <Panel>
            <SectionLabel icon={Database}>Terminal state</SectionLabel>
            <label className="mb-1.5 block font-mono text-[10px] tracking-[0.08em] text-text-faint uppercase" htmlFor="ticker-symbol">
              Ticker symbol
            </label>
            <div className="flex gap-2">
              <Input
                id="ticker-symbol"
                value={tickerInput}
                maxLength={32}
                placeholder="AAPL"
                onChange={(event) => setTickerInput(event.target.value)}
                autoComplete="off"
              />
              <ActionButton disabled={!tickerInput} onClick={() => setTickerInput("")}>Clear</ActionButton>
            </div>

            <label className="mt-4 mb-1.5 block font-mono text-[10px] tracking-[0.08em] text-text-faint uppercase">
              Role preview
            </label>
            <Select value={role} onValueChange={(value) => setRole(value as UserRole)}>
              <SelectTrigger className="w-full" aria-label="Role preview">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.values(UserRole).map((value) => (
                  <SelectItem key={value} value={value}>{ROLE_LABELS[value]}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="mt-5 flex items-start gap-2 border-t border-hairline pt-3 text-[11px] leading-relaxed text-text-dim">
              <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-blue" aria-hidden="true" />
              Role values mirror the backend RBAC contract; authentication will become authoritative in its dedicated phase.
            </div>
          </Panel>
        </div>
      </div>
    </main>
  );
}
