import { useState } from "react";

import { UserRole } from "@/entities/user";
import type { PMReviewDecision } from "@/entities/recommendation";
import { ActionButton, Chip } from "@/shared/ui";

const STATUS_COLOR = { pending_review: "var(--color-amber)", approved: "var(--color-green)", rejected: "var(--color-red)", deferred: "var(--color-text-dim)" } as const;

export function DecisionActions({ status, role, disabled, onDecision }: {
  status: keyof typeof STATUS_COLOR;
  role: UserRole;
  disabled?: boolean;
  onDecision: (decision: PMReviewDecision, rationale: string) => void;
}) {
  const [rationale, setRationale] = useState("");
  const isPortfolioManager = role === UserRole.PORTFOLIO_MANAGER;
  return (
    <div className="border-t border-hairline pt-3">
      <div className="flex items-center gap-2">
        <Chip color={STATUS_COLOR[status]}>{status.replaceAll("_", " ")}</Chip>
        {!isPortfolioManager ? <span className="font-mono text-[10px] text-text-faint">Read-only — Portfolio Manager role required</span> : null}
      </div>
      {isPortfolioManager ? <div className="mt-3 flex items-end gap-2"><label className="min-w-0 flex-1 font-mono text-[9px] tracking-wide text-text-faint uppercase">Decision rationale<textarea className="mt-1 block min-h-16 w-full resize-y rounded-terminal border border-hairline-bright bg-inset px-2.5 py-2 font-sans text-xs normal-case tracking-normal text-text-primary outline-none focus:border-amber/70" maxLength={4000} value={rationale} onChange={(event) => setRationale(event.target.value)} placeholder="Required by the review contract" /></label><div className="flex gap-1.5"><ActionButton disabled={disabled || !rationale.trim()} color="var(--color-green)" onClick={() => onDecision("approve", rationale)}>Approve</ActionButton><ActionButton disabled={disabled || !rationale.trim()} color="var(--color-red)" onClick={() => onDecision("reject", rationale)}>Reject</ActionButton><ActionButton disabled={disabled || !rationale.trim()} color="var(--color-text-dim)" onClick={() => onDecision("defer", rationale)}>Defer</ActionButton></div></div> : null}
    </div>
  );
}
