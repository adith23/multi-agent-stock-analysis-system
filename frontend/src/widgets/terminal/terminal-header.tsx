import { Hexagon, Radio } from "lucide-react";

import { UserRole } from "@/entities/user";
import { TickerSearchBar } from "@/features/ticker-search";
import { useClock } from "@/shared/hooks";
import { cn } from "@/shared/lib";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/shadcn";
import { useTerminalStore } from "@/stores/terminal-store";

const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.PORTFOLIO_MANAGER]: "Portfolio Manager",
  [UserRole.INVESTMENT_ANALYST]: "Investment Analyst",
  [UserRole.RESEARCH_ANALYST]: "Research Analyst",
  [UserRole.RISK_OFFICER]: "Risk Officer",
  [UserRole.COMPLIANCE_REVIEWER]: "Compliance Reviewer",
  [UserRole.SYSTEM_ADMINISTRATOR]: "System Administrator",
};

export function TerminalHeader({ onTickerSubmit, isSubmitting = false }: { onTickerSubmit: (ticker: string) => void; isSubmitting?: boolean }) {
  const clock = useClock();
  const role = useTerminalStore((state) => state.role);
  const systemState = useTerminalStore((state) => state.systemState);
  const setRole = useTerminalStore((state) => state.setRole);

  return (
    <header role="banner" className="flex h-terminal-header shrink-0 items-center gap-5 border-b border-hairline bg-panel px-3" aria-label="Terminal header">
      <div className="flex w-[208px] shrink-0 items-center gap-2.5">
        <span className="relative grid size-7 place-items-center text-amber" aria-hidden="true">
          <Hexagon className="absolute inset-0 size-7" strokeWidth={1.2} />
          <span className="font-serif text-[11px] font-bold">C</span>
        </span>
        <div>
          <div className="font-serif text-sm font-semibold tracking-[0.06em]">CONCLAVE</div>
          <div className="font-mono text-[7px] tracking-[0.18em] text-text-faint uppercase">Decision terminal</div>
        </div>
      </div>

      <TickerSearchBar onSubmit={onTickerSubmit} isSubmitting={isSubmitting} />

      <div className="ml-auto flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[8px] tracking-[0.12em] text-text-faint uppercase">Role preview</span>
          <Select value={role} onValueChange={(value) => setRole(value as UserRole)}>
            <SelectTrigger className="h-8 w-48" aria-label="Role preview">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.values(UserRole).map((value) => (
                <SelectItem key={value} value={value}>{ROLE_LABELS[value]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="h-7 w-px bg-hairline" aria-hidden="true" />

        <div className="flex items-center gap-2">
          <Radio
            className={cn("size-3", systemState === "running" ? "animate-pulse text-amber" : "text-green")}
            aria-hidden="true"
          />
          <span className="font-mono text-[8px] tracking-[0.08em] text-text-faint uppercase">
            {systemState === "running" ? "Simulation" : "System online"}
          </span>
        </div>

        <time className="w-[74px] text-right font-mono text-[11px] tabular-nums text-text-dim" dateTime={clock.toISOString()} suppressHydrationWarning>
          {clock.toLocaleTimeString("en-GB", { hour12: false })}
        </time>
      </div>
    </header>
  );
}
