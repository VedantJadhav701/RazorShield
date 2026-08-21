"use client";

import React, { useEffect, useState } from "react";
import { analyzeTransaction, resetDemoState } from "@/lib/api";
import { AnalyzeTransactionResponse, TransactionApiInput } from "@/lib/types";
import RiskOverviewCard from "@/components/dashboard/RiskOverviewCard";
import EvidenceGrid from "@/components/dashboard/EvidenceGrid";
import SLMExplanationCard from "@/components/dashboard/SLMExplanationCard";
import TransactionForm from "@/components/dashboard/TransactionForm";
import { ShieldCheck, RefreshCw, Cpu } from "lucide-react";

export default function DashboardPage() {
  const [analysisData, setAnalysisData] = useState<AnalyzeTransactionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState<"CONNECTED" | "CONNECTING">("CONNECTING");
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  // Initial load default transaction analysis
  useEffect(() => {
    handleAnalyze({
      merchant_id: "M_101",
      transaction_id: "TX_994182",
      customer_id: "C_1048",
      device_id: "D_882",
      amount: 125.50,
      payment_method: "card",
      transaction_type: "sale",
      policy_mode: "BALANCED",
    });
  }, []);

  const handleAnalyze = async (input: TransactionApiInput) => {
    setIsLoading(true);
    setResetMessage(null);
    try {
      const res = await analyzeTransaction(input);
      setAnalysisData(res);
      setApiStatus("CONNECTED");
    } catch (err) {
      console.error("Dashboard analysis error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    setIsLoading(true);
    try {
      const res = await resetDemoState();
      setResetMessage(res.message);
      // Re-run default transaction analysis
      await handleAnalyze({
        merchant_id: "M_101",
        transaction_id: "TX_RESET_01",
        amount: 100.0,
        policy_mode: "BALANCED",
      });
    } catch (err) {
      console.error("Reset error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-brand-black min-h-[calc(100vh-80px)] py-10">
      <div className="max-w-7xl mx-auto px-6 space-y-8">
        {/* Header Status Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-brand-border/60 pb-6">
          <div>
            <h1 className="font-sans font-bold text-3xl text-white tracking-tight">
              RazorShield Risk Console
            </h1>
            <p className="font-mono text-xs text-brand-muted mt-1">
              Real-Time Transaction Risk Analysis & Merchant Incident Monitoring
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="inline-flex items-center space-x-1.5 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-mono text-xs text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>API CONNECTED</span>
            </div>

            <div className="inline-flex items-center space-x-1.5 border border-brand-border bg-brand-dark px-3 py-1 font-mono text-xs text-white">
              <Cpu className="w-3.5 h-3.5 text-brand-red" />
              <span>SLM READY (Qwen2.5-0.5B)</span>
            </div>

            <button
              onClick={handleReset}
              disabled={isLoading}
              className="inline-flex items-center space-x-1.5 border border-brand-border hover:border-white text-brand-muted hover:text-white px-3 py-1 font-mono text-xs transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
              <span>RESET DEMO</span>
            </button>
          </div>
        </div>

        {resetMessage && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs p-3">
            {resetMessage}
          </div>
        )}

        {/* Top Grid: Risk Overview & Transaction Input Form */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 space-y-6">
            <RiskOverviewCard data={analysisData} />
            <EvidenceGrid data={analysisData} />
          </div>

          <div className="lg:col-span-5">
            <TransactionForm onSubmit={handleAnalyze} isLoading={isLoading} />
          </div>
        </div>

        {/* SLM Explanation Card */}
        <SLMExplanationCard data={analysisData} />
      </div>
    </div>
  );
}
