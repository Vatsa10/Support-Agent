import type { Metadata } from "next";
import { display, sans, mono } from "@/lib/fonts";
import { cn } from "@/lib/cn";
import "./globals.css";

export const metadata: Metadata = {
  title: "Resolve. — The AI operator that actually resolves.",
  description:
    "Resolve. is a multi-tenant AI customer support operator with authority to refund, replace, and close — not just chat.",
  metadataBase: new URL("https://resolve.example.com")
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={cn(display.variable, sans.variable, mono.variable)}>
      <body className="font-sans antialiased text-ink bg-paper">{children}</body>
    </html>
  );
}
