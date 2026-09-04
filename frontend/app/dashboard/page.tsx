"use client";

import React, { useEffect, useState } from "react";
import { analyzeTransaction, checkBackendHealth, resetDemoState } from "@/lib/api";
import {
  AnalyzeTransactionResponse,
  BackendHealthStatus,
  LogEventItem,
  ResponseMetadata,
  TransactionApiInput,
} from "@/lib/types";
import SystemStatusBar from "@/components/dashboard/SystemStatusBar";
import SystemActivityLog from "@/components/dashboard/SystemActivityLog";
import LiveStreamControls from "@/components/dashboard/LiveStreamControls";
import RiskOverviewCard from "@/components/dashboard/RiskOverviewCard";
import EvidenceGrid from "@/components/dashboard/EvidenceGrid";
import SLMExplanationCard from "@/components/dashboard/SLMExplanationCard";
import TransactionForm from "@/components/dashboard/TransactionForm";
import SLMChatDrawer from "@/components/dashboard/SLMChatDrawer";

export default function DashboardPage() {
  const [analysisData, setAnalysisData] = useState<AnalyzeTransactionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<BackendHealthStatus>({
    status: "CONNECTING",
    endpoint: process.env.NEXT_PUBLIC_API_URL || "https://vedantjadhav701-razorshield-api.hf.space",
    last_sync_at: null,
    roundtrip_latency_ms: null,
  });
  const [lastMeta, setLastMeta] = useState<ResponseMetadata | null>(null);
  const [lastOperation, setLastOperation] = useState<string>("NONE");
  const [logs, setLogs] = useState<LogEventItem[]>([]);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  // Probe real backend health on mount
  useEffect(() => {
    handleProbeHealth();
  }, []);

  const addLog = (
    eventType: LogEventItem["event_type"],
    operation: string,
    summary: string,
    merchantId?: string,
    latencyMs?: number,
    isError?: boolean
  ) => {
    const item: LogEventItem = {
      id: Math.random().toString(),
      timestamp: new Date().toISOString(),
      event_type: eventType,
      operation,
      summary,
      merchant_id: merchantId,
      latency_ms: latencyMs,
      is_error: isError,
    };
    setLogs((prev) => [item, ...prev].slice(0, 30));
  };

  const handleProbeHealth = async () => {
    setIsLoading(true);
    addLog("REQUEST_SENT", "health_check", "Probing live backend connectivity...");
    try {
      const res = await checkBackendHealth();
      setHealth(res);
      if (res.status === "CONNECTED") {
        addLog("RESPONSE_RECEIVED", "health_check", "Backend connection established", undefined, res.roundtrip_latency_ms || 0);
      } else {
        addLog("REQUEST_SENT", "health_check", "Backend offline / unreachable", undefined, undefined, true);
      }
    } catch (err) {
      console.error("Health probe error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async (input: TransactionApiInput) => {
    setIsLoading(true);
    setResetMessage(null);
    setLastOperation("analyze_transaction");

    addLog(
      "REQUEST_SENT",
      "analyze_transaction",
      `Evaluating ${input.merchant_id} / ${input.transaction_id} ($${input.amount})`,
      input.merchant_id
    );

    try {
      const res = await analyzeTransaction(input);
      setAnalysisData(res);
      if (res.meta) {
        setLastMeta(res.meta);
        addLog(
          "RESPONSE_RECEIVED",
          "analyze_transaction",
          `Decision: ${res.decision.action} (${res.merchant_risk.incident_state})`,
          input.merchant_id,
          res.meta.roundtrip_latency_ms
        );
      }
      setHealth((prev) => ({
        ...prev,
        status: "CONNECTED",
        last_sync_at: new Date().toISOString(),
        roundtrip_latency_ms: res.meta?.roundtrip_latency_ms || prev.roundtrip_latency_ms,
      }));
    } catch (err) {
      console.error("Dashboard analysis error:", err);
      addLog("REQUEST_SENT", "analyze_transaction", "Analysis request error", input.merchant_id, undefined, true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-secondary/30 min-h-[calc(100vh-80px)] py-10 font-body">
      <div className="max-w-7xl mx-auto px-6 space-y-8">
        {/* Title Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="font-display font-bold text-3xl sm:text-4xl text-foreground tracking-tight">
              RazorShield Operations Console
            </h1>
            <p className="font-body text-xs text-muted-foreground mt-1">
              Live Merchant Risk Monitoring & Real-Time Incident Intelligence Stream
            </p>
          </div>
        </div>

        {/* Real System Status Bar */}
        <SystemStatusBar
          health={health}
          lastMeta={lastMeta}
          lastOperation={lastOperation}
          onRefresh={handleProbeHealth}
          isLoading={isLoading}
        />

        {resetMessage && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 font-mono text-xs p-3 rounded-lg">
            {resetMessage}
          </div>
        )}

        {/* Live Stream Controls */}
        <LiveStreamControls onTransactionAnalyzed={(res) => setAnalysisData(res)} />

        {/* Main Grid: Risk Overview & Form */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 space-y-6">
            <RiskOverviewCard data={analysisData} />
            <EvidenceGrid data={analysisData} />
          </div>

          <div className="lg:col-span-5">
            <TransactionForm onSubmit={handleAnalyze} isLoading={isLoading} />
          </div>
        </div>

        {/* SLM Explanation */}
        <SLMExplanationCard data={analysisData} isLoading={isLoading} />

        {/* System Activity Trace Log */}
        <SystemActivityLog logs={logs} />
      </div>

      {/* Side SLM Chat Co-Pilot Drawer */}
      <SLMChatDrawer data={analysisData} />
    </div>
  );
}
