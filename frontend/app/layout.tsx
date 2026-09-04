import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";

export const metadata: Metadata = {
  title: "RazorShield — AI Merchant Risk & Fraud Intelligence",
  description:
    "Real-time calibrated transaction fraud scoring, temporal merchant incident detection, campaign-aware risk normalization, and zero-shot SLM explanations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light">
      <body className="bg-background text-foreground min-h-screen flex flex-col antialiased selection:bg-accent/20 selection:text-accent">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
