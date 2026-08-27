import { Providers } from "@/widgets/providers";

export default function TerminalLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <Providers>{children}</Providers>;
}
