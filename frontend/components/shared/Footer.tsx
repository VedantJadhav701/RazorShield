import React from "react";
import Link from "next/link";
import { Shield } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-brand-black border-t border-brand-border/60 py-12">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 bg-brand-red flex items-center justify-center text-white">
            <Shield className="w-4 h-4" />
          </div>
          <span className="font-sans font-bold text-sm tracking-wider text-white">
            RAZOR<span className="text-brand-red">SHIELD</span>
          </span>
          <span className="font-mono text-xs text-brand-muted">
            | AI Merchant Risk Intelligence
          </span>
        </div>

        <div className="flex items-center space-x-8 font-mono text-xs text-brand-muted">
          <Link href="/" className="hover:text-white transition-colors">Product</Link>
          <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
          <Link href="/scenarios" className="hover:text-white transition-colors">Scenarios</Link>
          <Link href="/evaluation" className="hover:text-white transition-colors">Evaluation</Link>
        </div>

        <div className="font-mono text-[11px] text-brand-muted">
          Internal Test-Set Benchmark Proven • Zero-Shot SLM Grounded
        </div>
      </div>
    </footer>
  );
}
