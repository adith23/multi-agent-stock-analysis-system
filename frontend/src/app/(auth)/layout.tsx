import { Providers } from "@/widgets/providers";

export default function AuthLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <Providers>{children}</Providers>;
}
