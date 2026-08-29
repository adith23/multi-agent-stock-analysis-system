import { Hexagon } from "lucide-react";
import type { Metadata } from "next";

import { LoginForm } from "@/features/auth";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to the Conclave institutional decision terminal.",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <main className="terminal-workspace-grid flex min-h-dvh items-center justify-center bg-void p-6">
      <div className="flex w-full max-w-[420px] flex-col items-center gap-5">
        <div className="flex items-center gap-3" aria-label="Conclave Decision Terminal">
          <span className="relative grid size-9 place-items-center text-amber" aria-hidden="true"><Hexagon className="absolute inset-0 size-9" strokeWidth={1.2} /><span className="font-serif text-sm font-bold">C</span></span>
          <div><p className="font-serif text-base font-semibold tracking-[0.08em]">CONCLAVE</p><p className="font-mono text-[8px] tracking-[0.2em] text-text-faint uppercase">Decision terminal</p></div>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
