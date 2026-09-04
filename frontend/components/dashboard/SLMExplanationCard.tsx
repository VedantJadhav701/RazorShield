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
      <div className="bg-background border border-border p-6 flex items-center justify-between font-body text-xs text-muted-foreground rounded-xl shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-2 h-2 rounded-full bg-accent animate-ping" />
          <span>Generating evidence explanation via NVIDIA GPT-5 SLM...</span>
        </div>
        <span className="text-[11px] font-mono text-muted-foreground">Model: NVIDIA GPT-5 SLM</span>
      </div>
    );
  }

  if (!data) return null;

  const exp = data.explanation;
  const isSlmGenerated = data.performance.slm_latency_ms > 0;

  return (
    <div className="bg-background border border-border p-6 flex flex-col justify-between rounded-xl shadow-sm font-body">
      <div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border pb-4 mb-6 gap-2 text-xs">
          <div className={`inline-flex items-center space-x-2 border px-3 py-1 font-mono text-[11px] uppercase font-bold rounded-full ${
            isSlmGenerated
              ? "bg-accent/10 border-accent/30 text-accent"
              : "bg-secondary border-border text-muted-foreground"
          }`}>
            <Cpu className="w-3.5 h-3.5" />
            <span>EXPLANATION SOURCE: {isSlmGenerated ? "NVIDIA GPT-5 / SLM API" : "DETERMINISTIC FALLBACK"}</span>
          </div>

          <div className="flex items-center space-x-3 text-muted-foreground text-[11px] font-mono">
            <span>SLM Latency: <strong className="text-emerald-600 font-semibold">{data.performance.slm_latency_ms} ms</strong></span>
            <span>|</span>
            <div className="flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Decision Authority: <strong className="text-foreground font-semibold">DETERMINISTIC RISK ENGINE</strong></span>
            </div>
          </div>
        </div>

        <h4 className="font-display font-bold text-2xl text-foreground mb-3">
          {exp.title}
        </h4>

        <p className="font-body text-muted-foreground text-sm leading-relaxed mb-6">
          {exp.summary}
        </p>

        {exp.key_signals && exp.key_signals.length > 0 && (
          <div className="mb-6">
            <span className="font-mono text-xs text-foreground uppercase font-bold block mb-2">
              Key Supporting Signals:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {exp.key_signals.map((sig, idx) => (
                <div
                  key={idx}
                  className="bg-secondary/40 border border-border px-3 py-2 font-mono text-xs text-muted-foreground rounded-md"
                >
                  • {sig}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs mb-6">
          <div className="bg-secondary/40 border border-border p-3 rounded-lg">
            <span className="text-muted-foreground block mb-1">Campaign Context:</span>
            <span className="text-foreground font-medium">{exp.campaign_context}</span>
          </div>

          <div className="bg-secondary/40 border border-border p-3 rounded-lg">
            <span className="text-muted-foreground block mb-1">Recommended Action:</span>
            <span className="text-rose-600 font-bold">{exp.recommended_action}</span>
          </div>
        </div>
      </div>

      <div className="bg-secondary/40 border border-border p-3 font-mono text-[11px] text-muted-foreground rounded-lg">
        {exp.confidence_note}
      </div>
    </div>
  );
}
