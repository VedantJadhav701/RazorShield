import React from "react";
import { CheckCircle2, ShieldCheck, Cpu, Database, Activity } from "lucide-react";

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
    { label: "Model Architecture", value: "Qwen/Qwen2.5-0.5B-Instruct" },
    { label: "Average GPU Latency", value: "472.03 ms" },
    { label: "P95 GPU Latency", value: "501.07 ms" },
    { label: "Grounding Benchmark Validity", value: "100.0%" },
    { label: "Measured Hallucination Rate", value: "0.00%" },
    { label: "VRAM Allocation", value: "943.91 MB" },
  ];

  return (
    <div className="bg-brand-black min-h-[calc(100vh-80px)] py-10">
      <div className="max-w-7xl mx-auto px-6 space-y-10">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between border-b border-brand-border/60 pb-6">
          <div>
            <span className="font-mono text-xs text-brand-red tracking-widest uppercase">
              // PROJECT PERFORMANCE REPORT
            </span>
            <h1 className="font-sans font-bold text-3xl text-white tracking-tight mt-1">
              Verified Measured Benchmark Results
            </h1>
          </div>
          <div className="flex flex-col items-end space-y-1 mt-4 sm:mt-0">
            <span className="font-mono text-xs text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-bold">
              EMPIRICAL BENCHMARKS — OFFLINE HELD-OUT TEST SET
            </span>
            <span className="font-mono text-[10px] text-brand-muted">
              (NOT LIVE PRODUCTION METRICS)
            </span>
          </div>
        </div>

        {/* Section 1: Dataset A Transaction Model */}
        <div className="bg-brand-black border border-brand-border p-6">
          <div className="flex items-center space-x-2 font-mono text-xs text-brand-red mb-4">
            <Activity className="w-4 h-4" />
            <span className="font-bold">DATASET A — IEEE-CIS TRANSACTION MODEL (XGBOOST + ISOTONIC CALIBRATION)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {datasetAMetrics.map((m, idx) => (
              <div key={idx} className="bg-brand-dark border border-brand-border/60 p-4">
                <span className="font-mono text-xs text-brand-muted block mb-1">{m.label}</span>
                <span className="font-sans font-bold text-2xl text-white">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 2: Dataset B Spike Model */}
        <div className="bg-brand-black border border-brand-border p-6">
          <div className="flex items-center space-x-2 font-mono text-xs text-brand-red mb-4">
            <Database className="w-4 h-4" />
            <span className="font-bold">DATASET B — DEPLOYABLE FRAUD-SPIKE DETECTOR MODEL (v2)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {datasetBMetrics.map((m, idx) => (
              <div key={idx} className="bg-brand-dark border border-brand-border/60 p-4">
                <span className="font-mono text-xs text-brand-muted block mb-1">{m.label}</span>
                <span className="font-sans font-bold text-2xl text-white">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 3: Merchant Incident Engine */}
        <div className="bg-brand-black border border-brand-border p-6">
          <div className="flex items-center space-x-2 font-mono text-xs text-brand-red mb-4">
            <ShieldCheck className="w-4 h-4" />
            <span className="font-bold">MERCHANT INCIDENT ENGINE — PERSISTENT ANOMALY DETECTION (N=2 WINDOWS)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {incidentEngineMetrics.map((m, idx) => (
              <div key={idx} className="bg-brand-dark border border-brand-border/60 p-4">
                <span className="font-mono text-[11px] text-brand-muted block mb-1">{m.label}</span>
                <span className="font-sans font-bold text-xl text-white">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: SLM Explanation Layer */}
        <div className="bg-brand-black border border-brand-border p-6">
          <div className="flex items-center space-x-2 font-mono text-xs text-brand-red mb-4">
            <Cpu className="w-4 h-4" />
            <span className="font-bold">ZEROGPU SLM EXPLANATION LAYER — QWEN2.5-0.5B-INSTRUCT BENCHMARK</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {slmMetrics.map((m, idx) => (
              <div key={idx} className="bg-brand-dark border border-brand-border/60 p-4">
                <span className="font-mono text-[11px] text-brand-muted block mb-1">{m.label}</span>
                <span className="font-sans font-bold text-xl text-white">{m.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
