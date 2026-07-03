import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Multi-Agent Stock Analysis Dashboard",
  description: "Institutional decision-support platform with multi-agent consensus, adversarial bull/bear reviews, and active risk validation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased bg-[#0b0f19] text-[#e2e8f0] min-h-screen">
        {children}
      </body>
    </html>
  );
}
