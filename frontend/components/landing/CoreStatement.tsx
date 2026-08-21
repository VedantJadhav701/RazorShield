import React from "react";

export default function CoreStatement() {
  return (
    <section className="bg-brand-black border-b border-brand-border/60 py-24 relative overflow-hidden">
      <div className="max-w-5xl mx-auto px-6 text-left">
        <div className="font-mono text-xs text-brand-red tracking-widest uppercase mb-4">
          // CORE INNOVATION
        </div>
        <h2 className="font-sans font-bold text-3xl sm:text-5xl text-white tracking-tight leading-tight mb-8">
          &quot;Volume is not fraud.&quot;
        </h2>
        <p className="font-sans text-xl sm:text-2xl text-brand-muted leading-relaxed font-normal">
          RazorShield measures the <span className="text-white font-medium">excess fraud signal</span> beyond expected merchant behavior.
        </p>
      </div>
    </section>
  );
}
