"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ShieldAlert, Cpu } from "lucide-react";
import { AnalyzeTransactionResponse } from "@/lib/types";

interface Props {
  data: AnalyzeTransactionResponse | null;
}

export default function RiskOverviewCard({ data }: Props) {
  if (!data) {
    return (
      <div className="bg-brand-card border border-brand-border p-6 font-mono text-xs text-brand-muted">
        No transaction analyzed yet. Submit a transaction or run a scenario replay.
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

  return (
    <div className="bg-brand-black border border-brand-border p-6 flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-brand-border/60 pb-4 mb-6">
        <div className="flex items-center space-x-2 font-mono text-xs text-brand-muted">
          <span>MERCHANT INCIDENT STATE</span>
        </div>
        <span className="font-mono text-xs text-brand-muted">
          Policy Mode: <span className="text-white font-semibold">{data.decision.policy_mode}</span>
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
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

      <div className="bg-brand-dark border border-brand-border/60 p-4 font-mono text-xs text-brand-muted flex items-center justify-between">
        <span>Decision Source:</span>
        <span className="text-white font-bold tracking-wider">
          DETERMINISTIC RISK ENGINE
        </span>
      </div>
    </div>
  );
}
