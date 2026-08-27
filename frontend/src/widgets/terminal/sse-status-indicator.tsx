import { Radio } from "lucide-react";

import type { SseConnectionStatus } from "@/shared/api";
import { cn } from "@/shared/lib";

export function SseStatusIndicator({ pipeline, alerts }: { pipeline: SseConnectionStatus; alerts: SseConnectionStatus }) {
  const status = summarizeStatus(pipeline, alerts);
  const presentation = {
    idle: { label: "SSE idle", color: "text-text-faint" },
    connecting: { label: "SSE connecting", color: "text-amber" },
    open: { label: "SSE live", color: "text-green" },
    reconnecting: { label: "SSE reconnecting", color: "text-amber" },
    closed: { label: "SSE closed", color: "text-red" },
    error: { label: "SSE unavailable", color: "text-red" },
  }[status];

  return (
    <div className="flex items-center gap-1.5" title={`Pipeline stream: ${pipeline}; alert stream: ${alerts}`} aria-label={presentation.label}>
      <Radio className={cn("size-3", presentation.color, (status === "connecting" || status === "reconnecting") && "animate-pulse")} aria-hidden="true" />
      <span className={cn("font-mono text-[8px] tracking-[0.08em] uppercase", presentation.color)}>{presentation.label}</span>
    </div>
  );
}

export function summarizeStatus(pipeline: SseConnectionStatus, alerts: SseConnectionStatus): SseConnectionStatus {
  const statuses = [pipeline, alerts];
  if (statuses.includes("error")) return "error";
  if (statuses.includes("reconnecting")) return "reconnecting";
  if (statuses.includes("connecting")) return "connecting";
  if (statuses.includes("open")) return "open";
  if (statuses.includes("closed")) return "closed";
  return "idle";
}
