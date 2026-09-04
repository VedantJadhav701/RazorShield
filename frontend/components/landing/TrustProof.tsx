import React from "react";

export default function TrustProof() {
  const metrics = [
    { value: "88.89%", label: "SCENARIO INCIDENT RECALL", sub: "Fraud-spike attack detection" },
    { value: "80.47%", label: "INCIDENT PRECISION", sub: "Persistent alert precision" },
    { value: "0.00%", label: "NORMAL FALSE ALERTS", sub: "Clean baseline scenario protection" },
    { value: "0.00%", label: "FLASH SALE FALSE ALERTS", sub: "Hard-negative volume surge isolation" },
  ];

  return (
    <section className="bg-background border-b border-border py-20 font-body">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between mb-12">
          <div>
            <span className="font-mono text-xs text-accent tracking-widest uppercase">
              // EMPIRICAL PROOF
            </span>
            <h3 className="font-display text-3xl sm:text-4xl text-foreground tracking-tight mt-2">
              Verified Risk Engine Performance
            </h3>
          </div>
          <span className="font-mono text-xs text-muted-foreground border border-border rounded-full px-3 py-1 mt-4 sm:mt-0 bg-secondary/50">
            Internal test-set benchmark
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((m, idx) => (
            <div key={idx} className="bg-secondary/30 border border-border p-6 flex flex-col justify-between rounded-xl shadow-sm">
              <span className="font-display font-bold text-4xl sm:text-5xl text-foreground tracking-tight mb-4">
                {m.value}
              </span>
              <div>
                <span className="font-mono text-xs font-bold text-foreground tracking-widest uppercase block mb-1">
                  {m.label}
                </span>
                <span className="font-body text-[11px] text-muted-foreground block">
                  {m.sub}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
