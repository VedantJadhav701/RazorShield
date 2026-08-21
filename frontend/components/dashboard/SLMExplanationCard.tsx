"use client";

import React from "react";
import { Cpu, ShieldCheck } from "lucide-react";
import { AnalyzeTransactionResponse } from "@/lib/types";

interface Props {
  data: AnalyzeTransactionResponse | null;
  isLoading?: boolean;
}

export default function SLMExplanationCard({ data, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="bg-brand-black border border-brand-border p-6 flex items-center justify-between font-mono text-xs text-brand-muted">
        <div className="flex items-center space-x-3">
          <div className="w-2 h-2 rounded-full bg-brand-red animate-ping" />
          <span>Generating evidence explanation (ZeroGPU dynamic allocation)...</span>
        </div>
        <span className="text-[11px] text-brand-muted">Model: Qwen2.5-0.5B-Instruct</span>
      </div>
    );
  }

  if (!data) return null;

  const exp = data.explanation;

  return (
    <div className="bg-brand-black border border-brand-border p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between border-b border-brand-border/60 pb-4 mb-6">
          <div className="inline-flex items-center space-x-2 bg-brand-red/10 border border-brand-red/30 px-3 py-1 font-mono text-[11px] text-brand-red uppercase">
            <Cpu className="w-3.5 h-3.5" />
            <span>AI-GENERATED EXPLANATION</span>
          </div>

          <div className="flex items-center space-x-2 font-mono text-xs text-brand-muted">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Decision Source: <strong className="text-white">DETERMINISTIC RISK ENGINE</strong></span>
          </div>
        </div>

        <h4 className="font-sans font-bold text-xl text-white mb-3">
          {exp.title}
        </h4>

        <p className="font-sans text-brand-muted text-sm leading-relaxed mb-6">
          {exp.summary}
        </p>

        {exp.key_signals && exp.key_signals.length > 0 && (
          <div className="mb-6">
            <span className="font-mono text-xs text-white uppercase font-bold block mb-2">
              Key Supporting Signals:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {exp.key_signals.map((sig, idx) => (
                <div
                  key={idx}
                  className="bg-brand-dark border border-brand-border/60 px-3 py-2 font-mono text-xs text-brand-muted"
                >
                  • {sig}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs mb-6">
          <div className="bg-brand-dark border border-brand-border/60 p-3">
            <span className="text-brand-muted block mb-1">Campaign Context:</span>
            <span className="text-white">{exp.campaign_context}</span>
          </div>

          <div className="bg-brand-dark border border-brand-border/60 p-3">
            <span className="text-brand-muted block mb-1">Recommended Action:</span>
            <span className="text-brand-red font-bold">{exp.recommended_action}</span>
          </div>
        </div>
      </div>

      <div className="bg-brand-dark border border-brand-border/60 p-3 font-mono text-[11px] text-brand-muted">
        {exp.confidence_note}
      </div>
    </div>
  );
}
