import * as React from "react";

import { cn } from "@/shared/lib/cn";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "flex h-8 w-full min-w-0 rounded-terminal border border-hairline-bright bg-inset px-2.5 py-1 font-mono text-xs text-text-primary outline-none transition-colors placeholder:text-text-faint focus-visible:border-amber/70 focus-visible:ring-2 focus-visible:ring-amber/20 disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-red aria-invalid:ring-red/20",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
