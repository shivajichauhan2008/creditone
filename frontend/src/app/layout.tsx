import type { Metadata } from "next";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import Link from "next/link";
import { ReportProvider } from "@/lib/store";
import "./globals.css";

export const metadata: Metadata = {
  title: "CreditOne: see what your credit report means for your month",
  description:
    "Upload your credit report and see what you owe, what you pay each month, what's left, and how to lift your score.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <ReportProvider>
          <header className="border-b border-line">
            <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
              <Link href="/" className="text-lg font-semibold tracking-tight">
                Credit<span className="text-marigold">One</span>
              </Link>
              <p className="text-sm text-muted">Your report is read, then deleted</p>
            </div>
          </header>
          <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8">{children}</main>
          <footer className="border-t border-line">
            <p className="mx-auto max-w-3xl px-4 py-5 text-xs leading-relaxed text-muted">
              CreditOne is not affiliated with any credit bureau and does not give financial
              advice. Figures marked as estimates are calculated, not taken from your report.
            </p>
          </footer>
        </ReportProvider>
      </body>
    </html>
  );
}
