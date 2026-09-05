"use client";

import * as React from "react";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";

import { cn } from "@/shared/lib/cn";

function ScrollArea({ className, children, ...props }: React.ComponentProps<typeof ScrollAreaPrimitive.Root>) {
  return (
    <ScrollAreaPrimitive.Root className={cn("relative overflow-hidden", className)} {...props}>
      <ScrollAreaPrimitive.Viewport className="size-full rounded-[inherit] outline-none focus-visible:ring-2 focus-visible:ring-amber/40">
        {children}
      </ScrollAreaPrimitive.Viewport>
      <ScrollBar />
      <ScrollAreaPrimitive.Corner />
    </ScrollAreaPrimitive.Root>
  );
}

function ScrollBar({
  className,
  orientation = "vertical",
  ...props
}: React.ComponentProps<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>) {
  return (
    <ScrollAreaPrimitive.ScrollAreaScrollbar
      orientation={orientation}
      className={cn(
        "flex touch-none p-px transition-colors select-none data-[orientation=horizontal]:h-2 data-[orientation=horizontal]:flex-col data-[orientation=vertical]:h-full data-[orientation=vertical]:w-2",
        className,
      )}
      {...props}
    >
      <ScrollAreaPrimitive.ScrollAreaThumb className="relative flex-1 rounded-full bg-hairline-bright" />
    </ScrollAreaPrimitive.ScrollAreaScrollbar>
  );
}

export { ScrollArea, ScrollBar };
