import type { CSSProperties, HTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export interface ChipProps extends HTMLAttributes<HTMLSpanElement> {
  color?: string;
  bg?: string;
  border?: string;
}

export function Chip({
  className,
  color = "var(--color-text-dim)",
  bg,
  border,
  style,
  ...props
}: ChipProps) {
  const dynamicStyles: CSSProperties = {
    color,
    backgroundColor: bg ?? `color-mix(in srgb, ${color} 10%, transparent)`,
    borderColor: border ?? `color-mix(in srgb, ${color} 42%, transparent)`,
    ...style,
  };

  return (
    <span
      className={cn(
        "inline-flex min-h-5 items-center rounded-terminal border px-2 py-0.5 font-mono text-[10px] font-medium tracking-[0.06em] uppercase",
        className,
      )}
      style={dynamicStyles}
      {...props}
    />
  );
}
