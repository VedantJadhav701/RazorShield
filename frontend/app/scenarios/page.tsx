"use client";

import React, { useState } from "react";
import { runScenarioReplay } from "@/lib/api";
import { ScenarioReplayResult } from "@/lib/types";
import { formatFixed } from "@/lib/utils";
import { Play, Loader2, CheckCircle2, AlertTriangle, ShieldAlert, Cpu, Radio, ShieldCheck } from "lucide-react";

export default function ScenariosPage() {
  const [selectedScenario, setSelectedScenario] = useState("FRAUD_SPIKE");
  const [policyMode, setPolicyMode] = useState("BALANCED");
  const [result, setResult] = useState<ScenarioReplayResult | null>(null);
  const [executionState, setExecutionState] = useState<"READY" | "RUNNING" | "COMPLETE" | "FAILED">("READY");

  const scenariosList = [
    {
      id: "NORMAL",
      name: "NORMAL SCENARIO",
      desc: "Baseline transaction stream with normal fraud excess ratio (~1.0x).",
      expected: "NORMAL",
    },
    {
      id: "VOLUME_ONLY_SPIKE",
      name: "FLASH SALE (VOLUME SURGE)",
      desc: "Legitimate volume surge (4.0x velocity) with normal fraud excess (~1.0x).",
      expected: "NORMAL (Hard-negative isolated)",
    },
    {
      id: "AMOUNT_SHIFT",
      name: "AMOUNT SHIFT (BULK ORDERS)",
      desc: "High average amount shift without fraud excess surge.",
      expected: "NORMAL",
    },
    {
      id: "FRAUD_SPIKE",
      name: "FRAUD SPIKE ATTACK",
      desc: "Persistent fraud attack surging fraud excess ratio (8.2x) across N=2 windows.",
      expected: "ALERT (Persistent Incident)",
    },
    {
      id: "FRAUD_DURING_FLASH_SALE",
      name: "FLASH SALE WITH FRAUD ATTACK",
      desc: "Promotional campaign registered + active fraud attack surging fraud excess.",
      expected: "ALERT (Campaign Aware)",
    },
  ];

  const handleRun = async () => {
    setExecutionState("RUNNING");
    setResult(null);
    try {
      const res = await runScenarioReplay(selectedScenario, policyMode);
      setResult(res);
      setExecutionState("COMPLETE");
    } catch (err) {
      console.error("Scenario replay error:", err);
      setExecutionState("FAILED");
    }
  };

  const isAlert = result?.final_incident_state === "ALERT";
  const isVerify = result?.final_incident_state === "INVESTIGATE";
  const Icon = isAlert ? ShieldAlert : isVerify ? AlertTriangle : CheckCircle2;
  const meta = result?.meta;

  return (
    <div className="bg-secondary/30 min-h-[calc(100vh-80px)] py-10 font-body">
      <div className="max-w-7xl mx-auto px-6 space-y-8">
        <div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl text-foreground tracking-tight">
            Interactive Scenario Replay Engine
          </h1>
          <p className="font-body text-xs text-muted-foreground mt-1">
            Execute 600-transaction scenario streams chronologically through the live backend
          </p>
        </div>

        {/* Scenario Selection Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {scenariosList.map((sc) => {
            const isSelected = selectedScenario === sc.id;
            return (
              <button
                key={sc.id}
                onClick={() => {
                  setSelectedScenario(sc.id);
                  setExecutionState("READY");
                  setResult(null);
                }}
                className={`p-4 border text-left flex flex-col justify-between transition-all rounded-xl shadow-sm ${
                  isSelected
                    ? "bg-background border-accent text-foreground shadow-md"
                    : "bg-background/80 border-border text-muted-foreground hover:border-accent/40 hover:text-foreground"
                }`}
              >
                <div>
                  <span className="font-mono text-xs font-bold block mb-2 uppercase">
                    {sc.name}
                  </span>
                  <span className="font-body text-[11px] block leading-relaxed mb-4">
                    {sc.desc}
                  </span>
                </div>
                <span className="font-mono text-[10px] text-emerald-600 block border-t border-border/60 pt-2 font-semibold">
                  Expected: {sc.expected}
                </span>
              </button>
            );
          })}
        </div>

        {/* Control Bar */}
        <div className="bg-background border border-border p-6 flex flex-col sm:flex-row items-center justify-between gap-4 rounded-xl shadow-sm">
          <div className="flex items-center space-x-4">
            <span className="font-mono text-xs text-muted-foreground uppercase">Policy Mode:</span>
            <select
              value={policyMode}
              onChange={(e) => setPolicyMode(e.target.value)}
              className="bg-secondary/40 border border-border text-foreground px-3 py-2 font-mono text-xs focus:outline-none focus:border-accent rounded-md"
            >
              <option value="CONSERVATIVE">CONSERVATIVE</option>
              <option value="BALANCED">BALANCED</option>
              <option value="HIGH_SENSITIVITY">HIGH_SENSITIVITY</option>
            </select>
          </div>

          <button
            onClick={handleRun}
            disabled={executionState === "RUNNING"}
            className="w-full sm:w-auto bg-primary hover:bg-primary/90 disabled:bg-muted text-primary-foreground font-body text-xs font-medium uppercase tracking-wider px-8 py-3 flex items-center justify-center space-x-2 transition-all rounded-md shadow-sm"
          >
            {executionState === "RUNNING" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>REPLAYING SCENARIO STREAM...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>RUN SCENARIO REPLAY</span>
              </>
            )}
          </button>
        </div>

        {/* Initial Ready State Card */}
        {executionState === "READY" && (
          <div className="bg-background border border-border p-8 text-center font-mono text-xs space-y-3 rounded-xl shadow-sm">
            <div className="flex items-center justify-center space-x-2 text-muted-foreground font-bold uppercase">
              <Radio className="w-4 h-4 text-muted-foreground" />
              <span>SCENARIO READY — {selectedScenario}</span>
            </div>
            <p className="text-muted-foreground text-[11px] max-w-md mx-auto font-body">
              Click &quot;RUN SCENARIO REPLAY&quot; to send scenario request to the live backend.
            </p>
          </div>
        )}

        {/* Running Loader Card */}
        {executionState === "RUNNING" && (
          <div className="bg-background border border-border p-8 text-center font-mono text-xs space-y-3 rounded-xl shadow-sm">
            <div className="flex items-center justify-center space-x-2 text-accent font-bold uppercase">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>PROCESSING SCENARIO STREAM...</span>
            </div>
            <p className="text-muted-foreground text-[11px] font-body">
              Executing scenario payload through backend risk engine & incident persistence state manager.
            </p>
          </div>
        )}

        {/* Execution Results */}
        {executionState === "COMPLETE" && result && (
          <div className="space-y-6">
            {result.error ? (
              <div className="bg-rose-50 border border-rose-200 p-6 font-mono text-xs text-rose-700 space-y-2 rounded-xl">
                <span className="font-bold uppercase block">SCENARIO REPLAY ERROR</span>
                <p>{result.error}</p>
              </div>
            ) : (
              <div className="bg-background border border-border p-6 space-y-6 rounded-xl shadow-sm">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border pb-4 gap-4">
                  <div>
                    <span className="font-mono text-xs text-accent uppercase font-bold block mb-1">
                      REPLAY EXECUTION COMPLETE
                    </span>
                    <h3 className="font-display font-bold text-2xl text-foreground">
                      {result.scenario_name} ({result.merchant_id || "M_DEMO"})
                    </h3>
                  </div>

                  <div className={`inline-flex items-center space-x-2 border px-4 py-2 font-mono text-xs uppercase font-bold rounded-full ${
                    isAlert
                      ? "bg-rose-50 border-rose-200 text-rose-700"
                      : isVerify
                      ? "bg-amber-50 border-amber-200 text-amber-700"
                      : "bg-emerald-50 border-emerald-200 text-emerald-700"
                  }`}>
                    <Icon className="w-4 h-4 stroke-[2.5]" />
                    <span>FINAL INCIDENT STATE: {result.final_incident_state || "NORMAL"}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono text-xs">
                  <div className="bg-secondary/40 border border-border p-4 rounded-lg">
                    <span className="text-muted-foreground block mb-1">Total Transactions:</span>
                    <span className="text-foreground text-xl font-bold">{result.total_transactions ?? 0}</span>
                  </div>

                  <div className="bg-secondary/40 border border-border p-4 rounded-lg">
                    <span className="text-muted-foreground block mb-1">Engine Processing Time:</span>
                    <span className="text-foreground text-xl font-bold">{formatFixed(result.replay_time_ms ?? 0, 1)} ms</span>
                  </div>

                  <div className="bg-secondary/40 border border-border p-4 rounded-lg">
                    <span className="text-muted-foreground block mb-1">Normal Windows:</span>
                    <span className="text-emerald-600 text-xl font-bold">{result.incident_state_distribution?.NORMAL ?? 0}</span>
                  </div>

                  <div className="bg-secondary/40 border border-border p-4 rounded-lg">
                    <span className="text-muted-foreground block mb-1">Alert Incident Windows:</span>
                    <span className="text-rose-600 text-xl font-bold">{result.incident_state_distribution?.ALERT ?? 0}</span>
                  </div>
                </div>

              {/* Data Provenance Footer */}
              {meta && (
                <div className="bg-secondary/40 border border-border p-4 font-mono text-[11px] flex flex-wrap justify-between gap-3 text-muted-foreground rounded-lg">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>DATA SOURCE: <strong className="text-emerald-600 font-semibold">{meta.data_source}</strong></span>
                  </div>
                  <div>API: <span className="text-foreground font-medium">run_scenario</span></div>
                  <div>REQUEST ID: <span className="text-foreground font-medium">{meta.request_id}</span></div>
                  <div>ROUNDTRIP LATENCY: <span className="text-emerald-600 font-semibold">{meta.roundtrip_latency_ms} ms</span></div>
                </div>
              )}
            </div>
          )}

            {/* Explanation */}
            {result.explanation && (
              <div className="bg-background border border-border p-6 space-y-4 rounded-xl shadow-sm">
                <div className="flex items-center space-x-2 font-mono text-xs text-accent">
                  <Cpu className="w-4 h-4" />
                  <span className="font-bold">AI-GENERATED SCENARIO EXPLANATION</span>
                </div>

                <h4 className="font-display font-bold text-xl text-foreground">
                  {result.explanation.title}
                </h4>

                <p className="font-body text-muted-foreground text-sm leading-relaxed">
                  {result.explanation.summary}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                  <div className="bg-secondary/40 border border-border p-3 rounded-lg">
                    <span className="text-muted-foreground block mb-1">Campaign Context:</span>
                    <span className="text-foreground font-medium">{result.explanation.campaign_context}</span>
                  </div>

                  <div className="bg-secondary/40 border border-border p-3 rounded-lg">
                    <span className="text-muted-foreground block mb-1">Recommended Action:</span>
                    <span className="text-rose-600 font-bold">{result.explanation.recommended_action}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
