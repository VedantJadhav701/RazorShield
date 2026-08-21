import React from "react";
import { Cpu, CheckCircle } from "lucide-react";

export default function SLMSection() {
  return (
    <section className="bg-brand-black border-b border-brand-border/60 py-20">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-6">
          <div className="inline-flex items-center space-x-2 bg-brand-border/40 border border-brand-border px-3 py-1 mb-6 font-mono text-xs text-brand-red uppercase">
            <Cpu className="w-3.5 h-3.5" />
            <span>EXPLANATION LAYER</span>
          </div>

          <h3 className="font-sans font-bold text-3xl sm:text-4xl text-white tracking-tight leading-tight mb-6">
            Qwen2.5-0.5B-Instruct <br /> Zero-Shot Explanation Engine
          </h3>

          <p className="font-sans text-brand-muted text-base sm:text-lg leading-relaxed mb-8">
            The SLM ONLY converts deterministic structured evidence into a concise, grounded natural-language explanation. It <span className="text-white font-medium">never determines fraud or modifies the authoritative risk decision</span>.
          </p>

          <div className="space-y-4 font-mono text-xs text-brand-muted">
            <div className="flex items-center space-x-3 text-white">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Strict JSON schema validation & Pydantic verification</span>
            </div>
            <div className="flex items-center space-x-3 text-white">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Zero-shot prompt constraint with zero ungrounded claims</span>
            </div>
            <div className="flex items-center space-x-3 text-white">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>Automatic deterministic fallback if model is unavailable</span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-brand-dark border border-brand-border p-6 flex flex-col justify-between">
            <span className="font-sans font-bold text-3xl sm:text-4xl text-white mb-4">
              ~472 ms
            </span>
            <span className="font-mono text-xs text-brand-muted uppercase">
              Average measured explanation latency
            </span>
          </div>

          <div className="bg-brand-dark border border-brand-border p-6 flex flex-col justify-between">
            <span className="font-sans font-bold text-3xl sm:text-4xl text-white mb-4">
              100%
            </span>
            <span className="font-mono text-xs text-brand-muted uppercase">
              Grounding benchmark validity
            </span>
          </div>

          <div className="bg-brand-dark border border-brand-border p-6 flex flex-col justify-between">
            <span className="font-sans font-bold text-3xl sm:text-4xl text-white mb-4">
              0%
            </span>
            <span className="font-mono text-xs text-brand-muted uppercase">
              Measured hallucination rate
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
