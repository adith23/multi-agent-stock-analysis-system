import { AlertTriangle, Database, LoaderCircle, RefreshCw } from "lucide-react";

import { normalizeApiError } from "@/shared/api";
import { cn } from "@/shared/lib";

import { ActionButton } from "./action-button";
import { Chip } from "./chip";

export function DataModeBadge({ remote, refreshing = false }: { remote: boolean; refreshing?: boolean }) {
  return (
    <Chip color={remote ? "var(--color-green)" : "var(--color-blue)"} className="gap-1">
      {refreshing ? <LoaderCircle className="size-3 animate-spin" aria-hidden="true" /> : <Database className="size-3" aria-hidden="true" />}
      {remote ? (refreshing ? "Refreshing API" : "Backend API") : "Typed fixture"}
    </Chip>
  );
}

export function FeatureLoading({ label }: { label: string }) {
  return (
    <div className="grid min-h-48 place-items-center border border-hairline bg-panel" role="status">
      <span className="flex items-center gap-2 font-mono text-[11px] text-text-dim">
        <LoaderCircle className="size-4 animate-spin text-amber" aria-hidden="true" />Loading {label}…
      </span>
    </div>
  );
}

export function FeatureError({ error, retry, className }: { error: unknown; retry?: () => void; className?: string }) {
  const apiError = normalizeApiError(error);
  return (
    <div className={cn("border border-red/40 bg-red/5 p-4", className)} role="alert">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-red" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] font-medium text-red">Backend data unavailable</p>
          <p className="mt-1 text-xs leading-relaxed text-text-dim">{apiError.message}</p>
        </div>
        {retry ? <ActionButton color="var(--color-red)" onClick={retry}><RefreshCw className="mr-1 size-3" />Retry</ActionButton> : null}
      </div>
    </div>
  );
}
