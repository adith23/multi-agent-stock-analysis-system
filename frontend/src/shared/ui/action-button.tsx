import type { ButtonHTMLAttributes, CSSProperties } from "react";

import { cn } from "@/shared/lib/cn";

export interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  color?: string;
}

export function ActionButton({
  className,
  color = "var(--color-amber)",
  style,
  type = "button",
  ...props
}: ActionButtonProps) {
  const dynamicStyles: CSSProperties = {
    color,
    backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
    borderColor: `color-mix(in srgb, ${color} 45%, transparent)`,
    ...style,
  };

  return (
    <button
      type={type}
      className={cn(
        "inline-flex min-h-8 items-center justify-center rounded-terminal border px-3.5 font-mono text-[11px] font-medium tracking-[0.04em] uppercase transition-[background-color,border-color,opacity] outline-none hover:brightness-125 focus-visible:ring-2 focus-visible:ring-amber/50 focus-visible:ring-offset-2 focus-visible:ring-offset-void disabled:pointer-events-none disabled:opacity-45",
        className,
      )}
      style={dynamicStyles}
      {...props}
    />
  );
}
