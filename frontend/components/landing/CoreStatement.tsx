import React from "react";

export default function CoreStatement() {
  return (
    <section className="bg-background border-b border-border py-24 relative overflow-hidden font-body">
      <div className="max-w-5xl mx-auto px-6 text-left">
        <div className="font-mono text-xs text-accent tracking-widest uppercase mb-4">
          // CORE INNOVATION
        </div>
        <h2 className="font-display text-4xl sm:text-6xl text-foreground tracking-tight leading-tight mb-6">
          &quot;Volume is not <span className="font-display italic font-normal text-brand-red">fraud</span>.&quot;
        </h2>
        <p className="font-body text-xl sm:text-2xl text-muted-foreground leading-relaxed font-normal">
          Nexora RazorShield measures the <span className="text-foreground font-semibold">excess fraud signal</span> beyond expected merchant behavior.
        </p>
      </div>
    </section>
  );
}
