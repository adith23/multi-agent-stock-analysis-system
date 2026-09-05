"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

import { ActionButton } from "@/shared/ui";

export default function TerminalError({
  error,
  reset,
}: Readonly<{ error: Error & { digest?: string }; reset: () => void }>) {
  useEffect(() => {
    console.error("Terminal route failed to render", error);
  }, [error]);

  return (
    <main className="grid min-h-dvh place-items-center bg-void p-8 text-text-primary">
      <section className="w-full max-w-md rounded-terminal border border-red/40 bg-panel p-6 text-center">
        <AlertTriangle className="mx-auto size-6 text-red" aria-hidden="true" />
        <h1 className="mt-3 font-serif text-xl font-semibold">Terminal unavailable</h1>
        <p className="mt-2 text-sm leading-relaxed text-text-dim">
          The terminal shell could not be rendered. Retry the route; no analysis was submitted by this screen.
        </p>
        <ActionButton className="mt-5" color="var(--color-red)" onClick={reset}>
          Retry
        </ActionButton>
      </section>
    </main>
  );
}
