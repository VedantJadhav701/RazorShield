"use client";

import React from "react";
import { ShieldCheck, RefreshCw, Cpu, Activity, AlertOctagon } from "lucide-react";
import { BackendHealthStatus, ResponseMetadata } from "@/lib/types";

interface Props {
  health: BackendHealthStatus;
  lastMeta: ResponseMetadata | null;
  lastOperation?: string;
  onRefresh: () => void;
  isLoading?: boolean;
}

export default function SystemStatusBar({
  health,
  lastMeta,
  lastOperation = "NONE",
  onRefresh,
  isLoading,
}: Props) {
  const isConnected = health.status === "CONNECTED";
  const isOffline = health.status === "OFFLINE";

  const statusBg = isConnected
    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
    : isOffline
    ? "bg-brand-red/10 border-brand-red/30 text-brand-red"
    : "bg-amber-500/10 border-amber-500/30 text-amber-400";

  return (
    <div className="bg-brand-black border border-brand-border p-4 font-mono text-xs space-y-3">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-brand-border/60 pb-3">
        <div className="flex items-center space-x-3">
          <div className={`inline-flex items-center space-x-1.5 border px-3 py-1 font-bold ${statusBg}`}>
            {isOffline ? (
              <AlertOctagon className="w-3.5 h-3.5" />
            ) : (
              <ShieldCheck className="w-3.5 h-3.5" />
            )}
            <span>BACKEND: {health.status}</span>
          </div>

          <div className="inline-flex items-center space-x-1.5 border border-brand-border bg-brand-dark px-3 py-1 text-white">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>RISK ENGINE: ONLINE</span>
          </div>

          <div className="inline-flex items-center space-x-1.5 border border-brand-border bg-brand-dark px-3 py-1 text-white">
            <Cpu className="w-3.5 h-3.5 text-brand-red" />
            <span>SLM: Qwen2.5-0.5B</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 border border-brand-border hover:border-white text-brand-muted hover:text-white px-3 py-1 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>PROBE BACKEND</span>
          </button>
        </div>
      </div>

      {/* Dynamic Metadata Provenance Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] text-brand-muted">
        <div>
          <span>ENDPOINT: </span>
          <span className="text-white font-semibold">{health.endpoint.replace("https://", "")}</span>
        </div>
        <div>
          <span>LAST SYNC: </span>
          <span className="text-white font-semibold">
            {health.last_sync_at ? new Date(health.last_sync_at).toLocaleTimeString() : "—"}
          </span>
        </div>
        <div>
          <span>LAST OPERATION: </span>
          <span className="text-white font-semibold">{lastOperation}</span>
        </div>
        <div>
          <span>ROUNDTRIP LATENCY: </span>
          <span className="text-white font-semibold">
            {lastMeta ? `${lastMeta.roundtrip_latency_ms} ms` : health.roundtrip_latency_ms ? `${health.roundtrip_latency_ms} ms` : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
