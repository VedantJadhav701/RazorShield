import React from "react";

export default function TrustProof() {
  const metrics = [
    { value: "88.89%", label: "SCENARIO INCIDENT RECALL", sub: "Fraud-spike attack detection" },
    { value: "80.47%", label: "INCIDENT PRECISION", sub: "Persistent alert precision" },
    { value: "0.00%", label: "NORMAL FALSE ALERTS", sub: "Clean baseline scenario protection" },
    { value: "0.00%", label: "FLASH SALE FALSE ALERTS", sub: "Hard-negative volume surge isolation" },
  ];

  return (
    <section className="bg-brand-dark border-b border-brand-border/60 py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between mb-12">
          <div>
            <span className="font-mono text-xs text-brand-red tracking-widest uppercase">
              // EMPIRICAL PROOF
            </span>
            <h3 className="font-sans font-bold text-2xl sm:text-4xl text-white tracking-tight mt-2">
              Verified Risk Engine Performance
            </h3>
          </div>
          <span className="font-mono text-xs text-brand-muted border border-brand-border px-3 py-1 mt-4 sm:mt-0">
            Internal test-set benchmark
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((m, idx) => (
            <div key={idx} className="bg-brand-black border border-brand-border p-6 flex flex-col justify-between">
              <span className="font-sans font-bold text-4xl sm:text-5xl text-white tracking-tight mb-4">
                {m.value}
              </span>
              <div>
                <span className="font-mono text-xs font-bold text-white tracking-widest uppercase block mb-1">
                  {m.label}
                </span>
                <span className="font-mono text-[11px] text-brand-muted block">
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
