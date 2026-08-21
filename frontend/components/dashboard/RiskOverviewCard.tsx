"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ShieldAlert, Radio } from "lucide-react";
import { AnalyzeTransactionResponse } from "@/lib/types";

interface Props {
  data: AnalyzeTransactionResponse | null;
}

export default function RiskOverviewCard({ data }: Props) {
  if (!data) {
    return (
      <div className="bg-brand-black border border-brand-border p-8 font-mono text-xs text-center space-y-3">
        <div className="flex items-center justify-center space-x-2 text-brand-muted uppercase font-bold">
          <Radio className="w-4 h-4 text-brand-muted" />
          <span>NO TRANSACTION ANALYZED</span>
        </div>
        <p className="text-brand-muted text-[11px] max-w-md mx-auto">
          Submit a transaction payload using the form or start the live demo stream to evaluate real-time merchant incident risk.
        </p>
      </div>
    );
  }

  const action = data.decision.action;
  const state = data.merchant_risk.incident_state;
  const severity = data.merchant_risk.severity;

  const isAlert = action === "ALERT" || state === "ALERT";
  const isVerify = action === "VERIFY" || state === "INVESTIGATE";

  const statusBg = isAlert
    ? "bg-brand-red/10 border-brand-red/40 text-brand-red"
    : isVerify
    ? "bg-amber-400/10 border-amber-400/40 text-amber-400"
    : "bg-emerald-400/10 border-emerald-400/40 text-emerald-400";

  const Icon = isAlert ? ShieldAlert : isVerify ? AlertTriangle : CheckCircle2;
  const meta = data.meta;

  return (
    <div className="bg-brand-black border border-brand-border p-6 flex flex-col justify-between space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-brand-border/60 pb-4 gap-2 font-mono text-xs">
        <div className="flex items-center space-x-2 text-brand-muted">
          <span>MERCHANT: <strong className="text-white">{data.merchant_id}</strong></span>
          <span>|</span>
          <span>TX: <strong className="text-white">{data.transaction_id}</strong></span>
        </div>
        <span className="text-brand-muted">
          Policy Mode: <span className="text-white font-semibold">{data.decision.policy_mode}</span>
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="font-mono text-xs text-brand-muted uppercase mb-1">
            Primary Decision State
          </div>
          <div className="font-sans font-bold text-4xl sm:text-5xl text-white tracking-tight">
            {state}
          </div>
        </div>

        <div className={`inline-flex items-center space-x-2 border px-4 py-2 font-mono text-xs uppercase font-bold ${statusBg}`}>
          <Icon className="w-4 h-4 stroke-[2.5]" />
          <span>ACTION: {action} ({severity} SEVERITY)</span>
        </div>
      </div>

      {/* Decision Authority & Provenance */}
      <div className="bg-brand-dark border border-brand-border/60 p-4 font-mono text-xs space-y-2">
        <div className="flex items-center justify-between text-brand-muted">
          <span>Decision Authority:</span>
          <span className="text-white font-bold tracking-wider">
            DETERMINISTIC RISK ENGINE
          </span>
        </div>

        {meta && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-brand-border/40 text-[10px] text-brand-muted">
            <div>
              <span>REQUEST ID: </span>
              <span className="text-white">{meta.request_id}</span>
            </div>
            <div>
              <span>PROVENANCE: </span>
              <span className="text-emerald-400">{meta.data_source}</span>
            </div>
            <div>
              <span>UPDATED: </span>
              <span className="text-white">{new Date(meta.response_received_at).toLocaleTimeString()}</span>
            </div>
            <div>
              <span>ROUNDTRIP: </span>
              <span className="text-emerald-400">{meta.roundtrip_latency_ms} ms</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
