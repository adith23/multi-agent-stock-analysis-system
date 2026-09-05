import type { CSSProperties, HTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export interface MeterProps extends Omit<HTMLAttributes<HTMLDivElement>, "children"> {
  value: number;
  limit?: number;
  height?: number;
}

function getMeterColor(ratio: number): string {
  if (ratio > 0.9) return "var(--color-red)";
  if (ratio > 0.7) return "var(--color-amber)";
  return "var(--color-green)";
}

export function Meter({ value, limit = 100, height = 6, className, style, ...props }: MeterProps) {
  const safeLimit = Number.isFinite(limit) && limit > 0 ? limit : 100;
  const safeValue = Number.isFinite(value) ? Math.max(0, value) : 0;
  const ratio = Math.min(safeValue / safeLimit, 1);
  const fillStyle: CSSProperties = {
    width: `${ratio * 100}%`,
    backgroundColor: getMeterColor(ratio),
  };

  return (
    <div
      className={cn("overflow-hidden rounded-full bg-inset ring-1 ring-hairline", className)}
      style={{ height, ...style }}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={safeLimit}
      aria-valuenow={Math.min(safeValue, safeLimit)}
      {...props}
    >
      <div className="h-full rounded-full transition-[width] duration-300" style={fillStyle} />
    </div>
  );
}
