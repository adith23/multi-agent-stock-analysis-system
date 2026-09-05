import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/shared/lib/cn";

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-terminal border px-2 py-0.5 font-mono text-[10px] font-medium tracking-[0.05em] whitespace-nowrap uppercase transition-colors focus-visible:ring-2 focus-visible:ring-amber/50",
  {
    variants: {
      variant: {
        default: "border-amber/40 bg-amber/10 text-amber",
        secondary: "border-hairline-bright bg-panel-raised text-text-dim",
        destructive: "border-red/40 bg-red/10 text-red",
        outline: "border-hairline-bright bg-transparent text-text-primary",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.ComponentPropsWithoutRef<"span">,
    VariantProps<typeof badgeVariants> {
  asChild?: boolean;
}

function Badge({ className, variant, asChild = false, ...props }: BadgeProps) {
  const Component = asChild ? Slot : "span";
  return <Component className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
