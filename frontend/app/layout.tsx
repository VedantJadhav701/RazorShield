import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";

export const metadata: Metadata = {
  title: "Nexora / RazorShield — AI Automation & Risk Intelligence",
  description:
    "Automate your busywork with intelligent agents that learn, adapt, and execute. Real-time calibrated transaction fraud and merchant risk intelligence.",
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
