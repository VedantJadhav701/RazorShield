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
      <div className="bg-background border border-border p-8 font-body text-xs text-center space-y-3 rounded-xl shadow-sm">
        <div className="flex items-center justify-center space-x-2 text-muted-foreground uppercase font-bold">
          <Radio className="w-4 h-4 text-muted-foreground" />
          <span>NO TRANSACTION ANALYZED</span>
        </div>
        <p className="text-muted-foreground text-[11px] max-w-md mx-auto">
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
    ? "bg-rose-50 border-rose-200 text-rose-700"
    : isVerify
    ? "bg-amber-50 border-amber-200 text-amber-700"
    : "bg-emerald-50 border-emerald-200 text-emerald-700";

  const Icon = isAlert ? ShieldAlert : isVerify ? AlertTriangle : CheckCircle2;
  const meta = data.meta;

  return (
    <div className="bg-background border border-border p-6 flex flex-col justify-between space-y-6 rounded-xl shadow-sm font-body">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border pb-4 gap-2 text-xs">
        <div className="flex items-center space-x-2 text-muted-foreground font-mono">
          <span>MERCHANT: <strong className="text-foreground">{data.merchant_id}</strong></span>
          <span>|</span>
          <span>TX: <strong className="text-foreground">{data.transaction_id}</strong></span>
        </div>
        <span className="text-muted-foreground font-mono">
          Policy Mode: <span className="text-foreground font-semibold">{data.decision.policy_mode}</span>
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="text-xs text-muted-foreground uppercase font-medium mb-1">
            Primary Decision State
          </div>
          <div className="font-display font-bold text-4xl sm:text-5xl text-foreground tracking-tight">
            {state}
          </div>
        </div>

        <div className={`inline-flex items-center space-x-2 border px-4 py-2 text-xs uppercase font-bold rounded-full ${statusBg}`}>
          <Icon className="w-4 h-4 stroke-[2.5]" />
          <span>ACTION: {action} ({severity} SEVERITY)</span>
        </div>
      </div>

      {/* Decision Authority & Provenance */}
      <div className="bg-secondary/40 border border-border p-4 text-xs space-y-2 rounded-lg font-mono">
        <div className="flex items-center justify-between text-muted-foreground">
          <span>Decision Authority:</span>
          <span className="text-foreground font-bold tracking-wider">
            DETERMINISTIC RISK ENGINE
          </span>
        </div>

        {meta && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-border text-[10px] text-muted-foreground">
            <div>
              <span>REQUEST ID: </span>
              <span className="text-foreground">{meta.request_id}</span>
            </div>
            <div>
              <span>PROVENANCE: </span>
              <span className="text-emerald-600 font-medium">{meta.data_source}</span>
            </div>
            <div>
              <span>UPDATED: </span>
              <span className="text-foreground">{new Date(meta.response_received_at).toLocaleTimeString()}</span>
            </div>
            <div>
              <span>ROUNDTRIP: </span>
              <span className="text-emerald-600 font-medium">{meta.roundtrip_latency_ms} ms</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
