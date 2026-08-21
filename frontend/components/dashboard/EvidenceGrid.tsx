"use client";

import React from "react";
import { AnalyzeTransactionResponse } from "@/lib/types";
import { formatFixed, formatPercent, safeNumber } from "@/lib/utils";

interface Props {
  data: AnalyzeTransactionResponse | null;
}

export default function EvidenceGrid({ data }: Props) {
  if (!data) return null;

  const fraudProb = safeNumber(data.transaction_risk?.fraud_probability, 0);
  const spikeProb = safeNumber(data.merchant_risk?.spike_probability, 0);
  const excessRatio = safeNumber(data.merchant_risk?.fraud_excess_ratio, 1.0);
  const velocityRatio = safeNumber(data.merchant_risk?.velocity_ratio, 1.0);
  const windows = safeNumber(data.merchant_risk?.suspicious_windows, 0);
  const campaignActive = Boolean(data.campaign?.active);

  const items = [
    {
      label: "Txn Fraud Probability",
      value: formatPercent(fraudProb),
      desc: "Isotonic Calibrated XGBoost",
      isElevated: fraudProb >= 0.30,
    },
    {
      label: "Merchant Spike Probability",
      value: formatPercent(spikeProb),
      desc: "15m Temporal Spike Model",
      isElevated: spikeProb >= 0.35,
    },
    {
      label: "Fraud Excess Ratio",
      value: `${formatFixed(excessRatio, 2)}x`,
      desc: "Estimated vs Baseline Fraud",
      isElevated: excessRatio >= 1.8,
    },
    {
      label: "Volume Velocity Ratio",
      value: `${formatFixed(velocityRatio, 2)}x`,
      desc: "Rolling vs Baseline Volume",
      isElevated: false,
    },
    {
      label: "Suspicious Windows",
      value: `${windows} windows`,
      desc: "Persistence Anomaly Count (N=2)",
      isElevated: windows >= 2,
    },
    {
      label: "Campaign Status",
      value: campaignActive ? "ACTIVE (FLASH SALE)" : "INACTIVE",
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
            className={`bg-brand-dark border p-4 font-mono text-xs flex flex-col justify-between space-y-2 ${
              item.isElevated
                ? "border-brand-red/60 text-brand-red"
                : "border-brand-border/60 text-white"
            }`}
          >
            <div>
              <span className="text-brand-muted text-[10px] block uppercase font-bold mb-1">
                {item.label}
              </span>
              <span className="text-2xl font-bold font-sans tracking-tight block">
                {item.value}
              </span>
            </div>

            <span className="text-brand-muted text-[10px] block border-t border-brand-border/40 pt-2">
              {item.desc}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
