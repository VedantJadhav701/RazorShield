import React from "react";
import { Activity, ShieldCheck, Zap, Cpu } from "lucide-react";

export default function InformationStrip() {
  const capabilities = [
    { icon: Activity, label: "TRANSACTION RISK", desc: "Isotonic Calibrated XGBoost" },
    { icon: ShieldCheck, label: "MERCHANT INCIDENTS", desc: "Persistent Anomaly Windowing (N=2)" },
    { icon: Zap, label: "CAMPAIGN AWARENESS", desc: "Volume Velocity Normalization" },
    { icon: Cpu, label: "GROUNDED AI", desc: "Zero-Shot NVIDIA GPT-5 SLM" },
  ];

  return (
    <section className="bg-secondary/40 border-y border-border py-6">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6">
        {capabilities.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-background border border-border flex items-center justify-center text-accent shadow-sm">
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-xs font-bold tracking-widest text-foreground uppercase">
                  {item.label}
                </span>
                <span className="font-body text-[11px] text-muted-foreground">
                  {item.desc}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
