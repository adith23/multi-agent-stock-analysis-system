import type { Metadata } from "next";

import { Providers } from "@/widgets/providers";

export const metadata: Metadata = {
  title: "Analysis Workspace",
  description: "Governed multi-agent investment analysis and decision-support workspace.",
  robots: { index: false, follow: false },
};

export default function TerminalLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <Providers>{children}</Providers>;
}
