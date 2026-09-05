import type { Metadata, Viewport } from "next";

import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/700.css";
import "@fontsource-variable/inter";
import "@fontsource-variable/source-serif-4";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Conclave Terminal",
    template: "%s | Conclave Terminal",
  },
  description:
    "Institutional decision-support terminal for governed multi-agent stock analysis.",
  applicationName: "Conclave Terminal",
  manifest: "/manifest.webmanifest",
  robots: { index: false, follow: false },
  openGraph: {
    title: "Conclave Terminal",
    description:
      "Institutional decision-support terminal for governed multi-agent stock analysis.",
    type: "website",
  },
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#0a0b0d",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-void font-sans text-text-primary antialiased">
        {children}
      </body>
    </html>
  );
}
