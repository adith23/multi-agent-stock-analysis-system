import { Clock3 } from "lucide-react";
import { Chip, Panel, SectionLabel } from "@/shared/ui";
import { useAuditStore } from "@/stores/audit-store";
import { MOCK_AUDIT_ENTRIES } from "../model/mock-audit-trail";

function time(timestamp: string): string { const value = new Date(timestamp); return Number.isNaN(value.getTime()) ? "--:--:--" : value.toLocaleTimeString("en-GB", { hour12: false }); }

export function AuditTrailPanel() {
  const localEntries = useAuditStore((state) => state.entries);
  const entries = [...localEntries, ...MOCK_AUDIT_ENTRIES];
  return <Panel className="max-w-[900px]"><div className="flex items-center justify-between"><SectionLabel icon={Clock3}>Audit trail</SectionLabel><Chip color="var(--color-blue)">Local + typed fixture</Chip></div><div className="mt-1 overflow-hidden border border-hairline" role="table" aria-label="Audit trail"><div className="grid grid-cols-[76px_155px_minmax(0,1fr)_90px] gap-2 bg-panel-raised px-2 py-1.5 font-mono text-[8px] tracking-wide text-text-faint uppercase" role="row"><span role="columnheader">Time</span><span role="columnheader">Actor</span><span role="columnheader">Action</span><span role="columnheader" className="text-right">Reference</span></div>{entries.map((entry, index) => <div key={entry.id} className="grid grid-cols-[76px_155px_minmax(0,1fr)_90px] gap-2 px-2 py-2 font-mono text-[10px] even:bg-inset" role="row"><time role="cell" className="text-text-faint" dateTime={entry.occurred_at}>{time(entry.occurred_at)}</time><span role="cell" className="truncate text-blue">{entry.actor_label}</span><span role="cell" className="min-w-0 text-text-primary">{entry.summary}{index < localEntries.length ? <span className="ml-2 text-[8px] text-amber">[{entry.sync_status}]</span> : null}</span><span role="cell" className="text-right text-text-faint">{entry.reference}</span></div>)}</div><p className="mt-2 font-mono text-[9px] text-text-faint">No audit-list API exists yet; server audit history is not fabricated.</p></Panel>;
}
