import type { HTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/shared/lib/cn";

export interface SectionLabelProps extends HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
  icon?: LucideIcon;
}

export function SectionLabel({ children, className, icon: Icon, ...props }: SectionLabelProps) {
  return (
    <h2
      className={cn(
        "mb-2.5 flex items-center gap-1.5 font-mono text-[10.5px] font-medium tracking-[0.12em] text-text-dim uppercase",
        className,
      )}
      {...props}
    >
      {Icon ? <Icon aria-hidden="true" className="size-3.5 text-amber" strokeWidth={1.75} /> : null}
      {children}
    </h2>
  );
}
