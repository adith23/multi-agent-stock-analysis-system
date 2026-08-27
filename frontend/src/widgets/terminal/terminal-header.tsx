import { Hexagon, LogOut, Radio, UserRound } from "lucide-react";

import { USER_ROLE_LABELS } from "@/entities/user";
import { useLogout } from "@/features/auth";
import { TickerSearchBar } from "@/features/ticker-search";
import { useClock } from "@/shared/hooks";
import { cn } from "@/shared/lib";
import { useAuthStore, useTerminalStore } from "@/stores";

export function TerminalHeader({ onTickerSubmit, isSubmitting = false }: { onTickerSubmit: (ticker: string) => void; isSubmitting?: boolean }) {
  const clock = useClock();
  const role = useTerminalStore((state) => state.role);
  const systemState = useTerminalStore((state) => state.systemState);
  const user = useAuthStore((state) => state.user);
  const authStatus = useAuthStore((state) => state.status);
  const logout = useLogout();

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
        <div className="flex items-center gap-2" aria-label="Authenticated identity">
          <UserRound className="size-3.5 text-amber" aria-hidden="true" />
          <div className="text-right">
            <p className="font-mono text-[9px] text-text-primary">{user?.username ?? (authStatus === "checking" ? "VERIFYING" : "SESSION")}</p>
            <p className="font-mono text-[7px] tracking-[0.08em] text-text-faint uppercase">{USER_ROLE_LABELS[role]}</p>
          </div>
          <button type="button" onClick={() => logout.mutate()} disabled={logout.isPending} className="grid size-7 place-items-center rounded-terminal border border-hairline text-text-faint transition-colors hover:border-red/50 hover:text-red disabled:opacity-50" aria-label="Sign out">
            <LogOut className="size-3.5" />
          </button>
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
