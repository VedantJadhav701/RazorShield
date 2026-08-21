"use client";

import React from "react";
import { AnalyzeTransactionResponse } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

interface Props {
  data: AnalyzeTransactionResponse | null;
}

export default function EvidenceGrid({ data }: Props) {
  if (!data) return null;

  const items = [
    {
      label: "Txn Fraud Probability",
      value: formatPercent(data.transaction_risk.fraud_probability),
      desc: "Isotonic Calibrated XGBoost",
      isElevated: data.transaction_risk.fraud_probability >= 0.30,
    },
    {
      label: "Merchant Spike Probability",
      value: formatPercent(data.merchant_risk.spike_probability),
      desc: "15m Temporal Spike Model",
      isElevated: data.merchant_risk.spike_probability >= 0.35,
    },
    {
      label: "Fraud Excess Ratio",
      value: `${data.merchant_risk.fraud_excess_ratio.toFixed(2)}x`,
      desc: "Estimated vs Baseline Fraud",
      isElevated: data.merchant_risk.fraud_excess_ratio >= 1.8,
    },
    {
      label: "Volume Velocity Ratio",
      value: `${data.merchant_risk.velocity_ratio.toFixed(2)}x`,
      desc: "Rolling vs Baseline Volume",
      isElevated: false,
    },
    {
      label: "Suspicious Windows",
      value: `${data.merchant_risk.suspicious_windows} windows`,
      desc: "Persistence Anomaly Count (N=2)",
      isElevated: data.merchant_risk.suspicious_windows >= 2,
    },
    {
      label: "Campaign Status",
      value: data.campaign.active ? "ACTIVE (FLASH SALE)" : "INACTIVE",
      desc: "Volume Velocity Normalization",
      isElevated: false,
    },
  ];

  return (
    <div className="bg-brand-black border border-brand-border p-6">
      <div className="font-mono text-xs text-brand-red tracking-widest uppercase mb-4">
        // STRUCTURED RISK EVIDENCE
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="bg-brand-dark border border-brand-border/60 p-4 flex flex-col justify-between"
          >
            <span className="font-mono text-[11px] text-brand-muted uppercase mb-1">
              {item.label}
            </span>
            <span
              className={`font-sans font-bold text-2xl mb-2 ${
                item.isElevated ? "text-brand-red" : "text-white"
              }`}
            >
              {item.value}
            </span>
            <span className="font-mono text-[10px] text-brand-muted">
              {item.desc}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
