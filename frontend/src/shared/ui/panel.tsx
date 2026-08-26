import type { CSSProperties, HTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

export interface PanelProps extends HTMLAttributes<HTMLElement> {
  borderColor?: string;
}

export function Panel({ className, borderColor, style, ...props }: PanelProps) {
  const dynamicStyles: CSSProperties = {
    borderColor: borderColor ?? undefined,
    ...style,
  };

  return (
    <section
      className={cn(
        "rounded-terminal border border-hairline bg-panel p-3.5 shadow-[0_1px_0_rgb(255_255_255/0.02)_inset]",
        className,
      )}
      style={dynamicStyles}
      {...props}
    />
  );
}
