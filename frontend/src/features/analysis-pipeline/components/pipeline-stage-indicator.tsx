import { Check, Circle, LoaderCircle, Minus, X } from "lucide-react";

import { cn } from "@/shared/lib";
import type { PipelineStageStatus } from "@/stores/pipeline-store";

const STATUS_LABELS: Record<PipelineStageStatus, string> = {
  pending: "Pending",
  running: "Running",
  done: "Complete",
  failed: "Failed",
  skipped: "Skipped",
};

export function PipelineStageIndicator({ status, stageName }: { status: PipelineStageStatus; stageName: string }) {
  const Icon = status === "done" ? Check : status === "running" ? LoaderCircle : status === "failed" ? X : status === "skipped" ? Minus : Circle;

  return (
    <span
      className={cn(
        "grid size-4 shrink-0 place-items-center rounded-full border",
        status === "pending" && "border-hairline-bright text-text-faint",
        status === "running" && "border-amber/50 bg-amber/10 text-amber",
        status === "done" && "border-green/45 bg-green/10 text-green",
        status === "failed" && "border-red/50 bg-red/10 text-red",
        status === "skipped" && "border-hairline text-text-faint",
      )}
      role="img"
      aria-label={`${stageName}: ${STATUS_LABELS[status]}`}
    >
      <Icon className={cn("size-2.5", status === "running" && "animate-spin")} strokeWidth={2.5} aria-hidden="true" />
    </span>
  );
}
