import React from "react";
import { ArrowUpRight, CheckCircle2, AlertTriangle, ShieldAlert } from "lucide-react";

export default function ScenarioPreview() {
  const scenarios = [
    {
      title: "NORMAL",
      subtitle: "Baseline merchant activity",
      volume: "1.0x",
      excess: "1.0x",
      persistence: "0 windows",
      decision: "NORMAL",
      statusColor: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10",
      icon: CheckCircle2,
    },
    {
      title: "FLASH SALE",
      subtitle: "Promotional surge (No fraud)",
      volume: "4.0x",
      excess: "1.0x",
      persistence: "0 windows",
      decision: "NORMAL",
      statusColor: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10",
      icon: CheckCircle2,
    },
    {
      title: "AMOUNT SHIFT",
      subtitle: "Bulk order shift (No fraud)",
      volume: "1.2x",
      excess: "1.1x",
      persistence: "0 windows",
      decision: "NORMAL",
      statusColor: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10",
      icon: CheckCircle2,
    },
    {
      title: "FRAUD SPIKE",
      subtitle: "Persistent fraud attack",
      volume: "4.0x",
      excess: "8.2x",
      persistence: "N = 2 windows",
      decision: "ALERT",
      statusColor: "text-brand-red border-brand-red/30 bg-brand-red/10",
      icon: ShieldAlert,
    },
  ];

  return (
    <section className="bg-brand-dark border-b border-brand-border/60 py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-12">
          <div>
            <span className="font-mono text-xs text-brand-red tracking-widest uppercase">
              // HARD-NEGATIVE PROTECTION
            </span>
            <h3 className="font-sans font-bold text-2xl sm:text-4xl text-white tracking-tight mt-2">
              Scenario Behavioral Distinction
            </h3>
          </div>
          <p className="font-mono text-xs text-brand-muted max-w-md mt-4 md:mt-0">
            Decoupling volume velocity surges from excess fraud signals to prevent hard-negative false alerts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {scenarios.map((sc, idx) => {
            const Icon = sc.icon;
            return (
              <div
                key={idx}
                className="bg-brand-black border border-brand-border p-6 flex flex-col justify-between hover:border-brand-border/80 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-sm font-bold text-white tracking-wider">
                      {sc.title}
                    </span>
                    <span className={`inline-flex items-center space-x-1 border px-2 py-0.5 font-mono text-[10px] uppercase font-semibold ${sc.statusColor}`}>
                      <Icon className="w-3 h-3" />
                      <span>{sc.decision}</span>
                    </span>
                  </div>

                  <p className="font-mono text-xs text-brand-muted mb-6">
                    {sc.subtitle}
                  </p>

                  <div className="space-y-3 font-mono text-xs border-t border-brand-border/40 pt-4">
                    <div className="flex justify-between">
                      <span className="text-brand-muted">Volume Velocity:</span>
                      <span className="text-white font-semibold">{sc.volume}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-brand-muted">Fraud Excess:</span>
                      <span className={sc.decision === "ALERT" ? "text-brand-red font-bold" : "text-white font-semibold"}>
                        {sc.excess}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-brand-muted">Persistence:</span>
                      <span className="text-white">{sc.persistence}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
