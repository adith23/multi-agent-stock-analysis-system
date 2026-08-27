"use client";

import { useState, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { AuthBootstrap } from "@/features/auth/components/auth-bootstrap";
import { createQueryClient } from "@/shared/api";
import { Toaster, TooltipProvider } from "@/shared/ui/shadcn";

export function Providers({ children }: Readonly<{ children: ReactNode }>) {
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthBootstrap>{children}</AuthBootstrap>
        <Toaster />
      </TooltipProvider>
      {process.env.NODE_ENV === "development" ? <ReactQueryDevtools initialIsOpen={false} /> : null}
    </QueryClientProvider>
  );
}
