import React from "react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-background border-t border-border py-12 font-body">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
            N
          </div>
          <span className="font-semibold text-sm tracking-tight text-foreground">
            Nexora <span className="font-mono text-xs text-muted-foreground font-normal">/ RazorShield</span>
          </span>
        </div>

        <div className="flex items-center space-x-8 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
          <Link href="/dashboard" className="hover:text-foreground transition-colors">Dashboard</Link>
          <Link href="/scenarios" className="hover:text-foreground transition-colors">Scenarios</Link>
          <Link href="/evaluation" className="hover:text-foreground transition-colors">Evaluation</Link>
        </div>

        <div className="text-[11px] text-muted-foreground font-mono">
          Internal Test-Set Benchmark Proven • Zero-Shot SLM Grounded
        </div>
      </div>
    </footer>
  );
}
