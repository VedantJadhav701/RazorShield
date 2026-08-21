import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function FinalCTA() {
  return (
    <section className="bg-brand-dark border-b border-brand-border/60 py-24 text-center">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="font-sans font-bold text-4xl sm:text-6xl text-white tracking-tight mb-6">
          See the risk engine in action.
        </h2>
        <p className="font-mono text-sm text-brand-muted max-w-xl mx-auto mb-10">
          Experience real-time calibrated transaction risk scoring, temporal merchant incident detection, and grounded SLM explanations.
        </p>

        <Link
          href="/dashboard"
          className="group relative inline-flex items-center space-x-3 bg-brand-red hover:bg-brand-red-hover text-white font-mono text-sm tracking-widest uppercase px-10 py-5 transition-colors rounded-none"
        >
          <span>LAUNCH RAZORSHIELD</span>
          <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </section>
  );
}
