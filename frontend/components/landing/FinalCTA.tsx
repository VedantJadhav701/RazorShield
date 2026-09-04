import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function FinalCTA() {
  return (
    <section className="bg-secondary/40 border-b border-border py-24 text-center font-body">
      <div className="max-w-4xl mx-auto px-6">
        <h2 className="font-display text-4xl sm:text-6xl text-foreground tracking-tight mb-6">
          See the intelligence engine in action.
        </h2>
        <p className="font-body text-base text-muted-foreground max-w-xl mx-auto mb-10">
          Experience real-time calibrated transaction risk scoring, temporal merchant incident detection, and grounded SLM explanations with Nexora RazorShield.
        </p>

        <Link
          href="/dashboard"
          className="group inline-flex items-center space-x-3 bg-primary text-primary-foreground hover:bg-primary/90 font-body text-sm font-medium px-8 py-4 rounded-full transition-all shadow-md"
        >
          <span>Book a demo</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </section>
  );
}
