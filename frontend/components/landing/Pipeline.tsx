import React from "react";
import { ArrowRight } from "lucide-react";

export default function Pipeline() {
  const steps = [
    { title: "TRANSACTION", desc: "API Event Payload" },
    { title: "FRAUD PROBABILITY", desc: "Isotonic Calibrated XGBoost" },
    { title: "MERCHANT STATE", desc: "15m Rolling Temporal Window" },
    { title: "FRAUD EXCESS", desc: "Deployable Signal Extraction" },
    { title: "INCIDENT PERSISTENCE", desc: "N=2 Window Anomaly Counter" },
    { title: "RISK DECISION", desc: "APPROVE / VERIFY / ALERT" },
    { title: "SLM EXPLANATION", desc: "Qwen2.5-0.5B Zero-Shot Output" },
  ];

  return (
    <section className="bg-brand-black border-b border-brand-border/60 py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-12">
          <span className="font-mono text-xs text-brand-red tracking-widest uppercase">
            // TECHNICAL ARCHITECTURE
          </span>
          <h3 className="font-sans font-bold text-2xl sm:text-4xl text-white tracking-tight mt-2">
            Multi-Layer Risk Pipeline
          </h3>
        </div>

        {/* Horizontal Flow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-4">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="bg-brand-dark border border-brand-border p-4 flex flex-col justify-between relative group hover:border-brand-red/60 transition-colors"
            >
              <div>
                <span className="font-mono text-[10px] text-brand-red font-bold block mb-2">
                  0{idx + 1}
                </span>
                <span className="font-mono text-xs font-bold text-white tracking-wider block mb-2">
                  {step.title}
                </span>
                <span className="font-mono text-[11px] text-brand-muted block">
                  {step.desc}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10 text-brand-border group-hover:text-brand-red transition-colors">
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
