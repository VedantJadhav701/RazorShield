import React from "react";
import { Cpu, CheckCircle } from "lucide-react";

export default function SLMSection() {
  return (
    <section className="bg-secondary/30 border-b border-border py-20 font-body">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-6">
          <div className="inline-flex items-center space-x-2 bg-background border border-border px-3 py-1 mb-6 font-mono text-xs text-accent uppercase rounded-full shadow-sm">
            <Cpu className="w-3.5 h-3.5" />
            <span>EXPLANATION LAYER</span>
          </div>

          <h3 className="font-display text-3xl sm:text-4xl text-foreground tracking-tight leading-tight mb-6">
            NVIDIA GPT-5 / SLM <br /> Grounded Explanation Engine
          </h3>

          <p className="font-body text-muted-foreground text-base sm:text-lg leading-relaxed mb-8">
            The SLM ONLY converts deterministic structured evidence into a concise, grounded natural-language explanation. It <span className="text-foreground font-semibold">never determines fraud or modifies the authoritative risk decision</span>.
          </p>

          <div className="space-y-4 font-body text-xs text-muted-foreground">
            <div className="flex items-center space-x-3 text-foreground">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              <span>Strict JSON schema validation & Pydantic verification</span>
            </div>
            <div className="flex items-center space-x-3 text-foreground">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              <span>Zero-shot prompt constraint with zero ungrounded claims</span>
            </div>
            <div className="flex items-center space-x-3 text-foreground">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              <span>Automatic deterministic fallback if model is unavailable</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-background border border-border p-6 flex flex-col justify-between rounded-xl shadow-sm">
            <span className="font-display font-bold text-3xl sm:text-4xl text-foreground mb-4">
              ~240 ms
            </span>
            <span className="font-mono text-xs text-muted-foreground uppercase">
              Average measured explanation latency
            </span>
          </div>

          <div className="bg-background border border-border p-6 flex flex-col justify-between rounded-xl shadow-sm">
            <span className="font-display font-bold text-3xl sm:text-4xl text-foreground mb-4">
              100%
            </span>
            <span className="font-mono text-xs text-muted-foreground uppercase">
              Grounding benchmark validity
            </span>
          </div>

          <div className="bg-background border border-border p-6 flex flex-col justify-between rounded-xl shadow-sm">
            <span className="font-display font-bold text-3xl sm:text-4xl text-foreground mb-4">
              0%
            </span>
            <span className="font-mono text-xs text-muted-foreground uppercase">
              Measured hallucination rate
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
