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
    { title: "SLM EXPLANATION", desc: "NVIDIA GPT-5 SLM Output" },
  ];

  return (
    <section className="bg-background border-b border-border py-20 font-body">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-12">
          <span className="font-mono text-xs text-accent tracking-widest uppercase">
            // TECHNICAL ARCHITECTURE
          </span>
          <h3 className="font-display text-3xl sm:text-4xl text-foreground tracking-tight mt-2">
            Multi-Layer Risk Pipeline
          </h3>
        </div>

        {/* Horizontal Flow */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-4">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="bg-secondary/40 border border-border p-4 flex flex-col justify-between relative group hover:border-accent/60 transition-colors rounded-xl shadow-sm"
            >
              <div>
                <span className="font-mono text-[10px] text-accent font-bold block mb-2">
                  0{idx + 1}
                </span>
                <span className="font-mono text-xs font-bold text-foreground tracking-wider block mb-2">
                  {step.title}
                </span>
                <span className="font-body text-[11px] text-muted-foreground block">
                  {step.desc}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10 text-border group-hover:text-accent transition-colors">
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
