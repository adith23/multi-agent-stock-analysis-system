import { AlertCircle, CheckCircle2, XCircle } from "lucide-react";

import type { DataSourceHealth as DataSourceHealthModel } from "@/entities/portfolio";
import { cn } from "@/shared/lib";

const STATUS_DETAILS = {
  ok: { label: "Healthy", className: "text-green", icon: CheckCircle2 },
  delayed: { label: "Delayed", className: "text-amber", icon: AlertCircle },
  down: { label: "Unavailable", className: "text-red", icon: XCircle },
} as const;

function formatSyncTime(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: "Asia/Colombo",
  }).format(date);
}

export function DataSourceHealth({ source }: { source: DataSourceHealthModel }) {
  const details = STATUS_DETAILS[source.status];
  const Icon = details.icon;

  return (
    <li className="flex items-center gap-2 py-1.5">
      <Icon className={cn("size-3 shrink-0", details.className)} strokeWidth={1.8} aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate text-[10px] text-text-dim">{source.name}</span>
      <span className="font-mono text-[8px] text-text-faint" aria-label={`${details.label}, last sync ${formatSyncTime(source.last_sync)}`}>
        {formatSyncTime(source.last_sync)}
      </span>
    </li>
  );
}
