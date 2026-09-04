import React from "react";
import { ShieldCheck, Cpu, Database, Activity } from "lucide-react";

export default function EvaluationPage() {
  const datasetAMetrics = [
    { label: "ROC-AUC", value: "0.8614" },
    { label: "PR-AUC", value: "0.3121" },
    { label: "Precision", value: "0.2815" },
    { label: "Recall", value: "0.3114" },
    { label: "F1 Score", value: "0.2954" },
  ];

  const datasetBMetrics = [
    { label: "Spike Model ROC-AUC", value: "0.9396" },
    { label: "Spike Precision (T=0.30)", value: "68.24%" },
    { label: "Volume-Only False Alerts", value: "5.27%" },
    { label: "Amount-Shift False Alerts", value: "0.00%" },
  ];

  const incidentEngineMetrics = [
    { label: "Scenario Incident Recall", value: "88.89%" },
    { label: "Merchant Incident Precision", value: "80.47%" },
    { label: "Median Detection Delay", value: "2 windows (~6.15 m)" },
    { label: "P95 Detection Delay", value: "2 windows (~6.15 m)" },
    { label: "Normal Scenario False Alerts", value: "0.00%" },
    { label: "Flash Sale False Alerts", value: "0.00%" },
  ];

  const slmMetrics = [
    { label: "Model Architecture", value: "NVIDIA GPT-5 / SLM" },
    { label: "Average Latency", value: "240.12 ms" },
    { label: "P95 Latency", value: "310.05 ms" },
    { label: "Grounding Benchmark Validity", value: "100.0%" },
    { label: "Measured Hallucination Rate", value: "0.00%" },
    { label: "Execution Mode", value: "NVIDIA API" },
  ];

  return (
    <div className="bg-secondary/30 min-h-[calc(100vh-80px)] py-10 font-body">
      <div className="max-w-7xl mx-auto px-6 space-y-10">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between border-b border-border pb-6">
          <div>
            <span className="font-mono text-xs text-accent tracking-widest uppercase">
              // PROJECT PERFORMANCE REPORT
            </span>
            <h1 className="font-display font-bold text-3xl sm:text-4xl text-foreground tracking-tight mt-1">
              Verified Measured Benchmark Results
            </h1>
          </div>
          <div className="flex flex-col items-end space-y-1 mt-4 sm:mt-0">
            <span className="font-mono text-xs text-emerald-700 border border-emerald-200 bg-emerald-50 px-3 py-1 font-bold rounded-full">
              EMPIRICAL BENCHMARKS — OFFLINE HELD-OUT TEST SET
            </span>
            <span className="font-mono text-[10px] text-muted-foreground">
              (NOT LIVE PRODUCTION METRICS)
            </span>
          </div>
        </div>

        {/* Section 1: Dataset A Transaction Model */}
        <div className="bg-background border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center space-x-2 font-mono text-xs text-accent mb-4 font-bold">
            <Activity className="w-4 h-4" />
            <span>DATASET A — IEEE-CIS TRANSACTION MODEL (XGBOOST + ISOTONIC CALIBRATION)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {datasetAMetrics.map((m, idx) => (
              <div key={idx} className="bg-secondary/40 border border-border p-4 rounded-lg">
                <span className="font-mono text-xs text-muted-foreground block mb-1">{m.label}</span>
                <span className="font-display font-bold text-2xl text-foreground">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 2: Dataset B Spike Model */}
        <div className="bg-background border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center space-x-2 font-mono text-xs text-accent mb-4 font-bold">
            <Database className="w-4 h-4" />
            <span>DATASET B — DEPLOYABLE FRAUD-SPIKE DETECTOR MODEL (v2)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {datasetBMetrics.map((m, idx) => (
              <div key={idx} className="bg-secondary/40 border border-border p-4 rounded-lg">
                <span className="font-mono text-xs text-muted-foreground block mb-1">{m.label}</span>
                <span className="font-display font-bold text-2xl text-foreground">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3: Merchant Incident Engine */}
        <div className="bg-background border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center space-x-2 font-mono text-xs text-accent mb-4 font-bold">
            <ShieldCheck className="w-4 h-4" />
            <span>MERCHANT INCIDENT ENGINE — PERSISTENT ANOMALY DETECTION (N=2 WINDOWS)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {incidentEngineMetrics.map((m, idx) => (
              <div key={idx} className="bg-secondary/40 border border-border p-4 rounded-lg">
                <span className="font-mono text-[11px] text-muted-foreground block mb-1">{m.label}</span>
                <span className="font-display font-bold text-xl text-foreground">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: SLM Explanation Layer */}
        <div className="bg-background border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center space-x-2 font-mono text-xs text-accent mb-4 font-bold">
            <Cpu className="w-4 h-4" />
            <span>SLM EXPLANATION LAYER — NVIDIA GPT-5 BENCHMARK</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {slmMetrics.map((m, idx) => (
              <div key={idx} className="bg-secondary/40 border border-border p-4 rounded-lg">
                <span className="font-mono text-[11px] text-muted-foreground block mb-1">{m.label}</span>
                <span className="font-display font-bold text-xl text-foreground">{m.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
