import React from "react";
import { CheckCircle2, ShieldAlert } from "lucide-react";

export default function ScenarioPreview() {
  const scenarios = [
    {
      title: "NORMAL",
      subtitle: "Baseline merchant activity",
      volume: "1.0x",
      excess: "1.0x",
      persistence: "0 windows",
      decision: "NORMAL",
      statusColor: "text-emerald-700 border-emerald-200 bg-emerald-50",
      icon: CheckCircle2,
    },
    {
      title: "FLASH SALE",
      subtitle: "Promotional surge (No fraud)",
      volume: "4.0x",
      excess: "1.0x",
      persistence: "0 windows",
      decision: "NORMAL",
      statusColor: "text-emerald-700 border-emerald-200 bg-emerald-50",
      icon: CheckCircle2,
    },
    {
      title: "AMOUNT SHIFT",
      subtitle: "Bulk order shift (No fraud)",
      volume: "1.2x",
      excess: "1.1x",
      persistence: "0 windows",
      decision: "NORMAL",
      statusColor: "text-emerald-700 border-emerald-200 bg-emerald-50",
      icon: CheckCircle2,
    },
    {
      title: "FRAUD SPIKE",
      subtitle: "Persistent fraud attack",
      volume: "4.0x",
      excess: "8.2x",
      persistence: "N = 2 windows",
      decision: "ALERT",
      statusColor: "text-rose-700 border-rose-200 bg-rose-50",
      icon: ShieldAlert,
    },
  ];

  return (
    <section className="bg-secondary/30 border-b border-border py-20 font-body">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-start md:items-end justify-between mb-12">
          <div>
            <span className="font-mono text-xs text-accent tracking-widest uppercase">
              // HARD-NEGATIVE PROTECTION
            </span>
            <h3 className="font-display text-3xl sm:text-4xl text-foreground tracking-tight mt-2">
              Scenario Behavioral Distinction
            </h3>
          </div>
          <p className="font-body text-sm text-muted-foreground max-w-md mt-4 md:mt-0">
            Decoupling volume velocity surges from excess fraud signals to prevent hard-negative false alerts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {scenarios.map((sc, idx) => {
            const Icon = sc.icon;
            return (
              <div
                key={idx}
                className="bg-background border border-border p-6 flex flex-col justify-between rounded-xl shadow-sm hover:shadow-md transition-all"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-sm font-bold text-foreground tracking-wider">
                      {sc.title}
                    </span>
                    <span className={`inline-flex items-center space-x-1 border px-2 py-0.5 font-mono text-[10px] uppercase font-semibold rounded-full ${sc.statusColor}`}>
                      <Icon className="w-3 h-3" />
                      <span>{sc.decision}</span>
                    </span>
                  </div>

                  <p className="font-body text-xs text-muted-foreground mb-6">
                    {sc.subtitle}
                  </p>

                  <div className="space-y-3 font-mono text-xs border-t border-border pt-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Volume Velocity:</span>
                      <span className="text-foreground font-semibold">{sc.volume}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Fraud Excess:</span>
                      <span className={sc.decision === "ALERT" ? "text-rose-600 font-bold" : "text-foreground font-semibold"}>
                        {sc.excess}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Persistence:</span>
                      <span className="text-foreground">{sc.persistence}</span>
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
