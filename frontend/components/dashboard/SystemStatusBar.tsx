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
    ? "bg-emerald-50 border-emerald-200 text-emerald-700"
    : isOffline
    ? "bg-rose-50 border-rose-200 text-rose-700"
    : "bg-amber-50 border-amber-200 text-amber-700";

  return (
    <div className="bg-background border border-border p-4 font-mono text-xs space-y-3 rounded-xl shadow-sm">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border pb-3">
        <div className="flex items-center space-x-3 flex-wrap gap-2">
          <div className={`inline-flex items-center space-x-1.5 border px-3 py-1 font-bold rounded-full ${statusBg}`}>
            {isOffline ? (
              <AlertOctagon className="w-3.5 h-3.5" />
            ) : (
              <ShieldCheck className="w-3.5 h-3.5" />
            )}
            <span>BACKEND: {health.status}</span>
          </div>

          <div className="inline-flex items-center space-x-1.5 border border-border bg-secondary/50 px-3 py-1 text-foreground rounded-full">
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            <span>RISK ENGINE: ONLINE</span>
          </div>

          <div className="inline-flex items-center space-x-1.5 border border-border bg-secondary/50 px-3 py-1 text-foreground rounded-full">
            <Cpu className="w-3.5 h-3.5 text-accent" />
            <span>SLM: NVIDIA GPT-5 SLM</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 border border-border hover:border-accent text-muted-foreground hover:text-foreground px-3 py-1.5 transition-colors rounded-lg bg-secondary/30"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>PROBE BACKEND</span>
          </button>
        </div>
      </div>

      {/* Dynamic Metadata Provenance Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] text-muted-foreground">
        <div>
          <span>ENDPOINT: </span>
          <span className="text-foreground font-semibold">{health.endpoint.replace("https://", "")}</span>
        </div>
        <div>
          <span>LAST SYNC: </span>
          <span className="text-foreground font-semibold">
            {health.last_sync_at ? new Date(health.last_sync_at).toLocaleTimeString() : "—"}
          </span>
        </div>
        <div>
          <span>LAST OPERATION: </span>
          <span className="text-foreground font-semibold">{lastOperation}</span>
        </div>
        <div>
          <span>ROUNDTRIP LATENCY: </span>
          <span className="text-foreground font-semibold">
            {lastMeta ? `${lastMeta.roundtrip_latency_ms} ms` : health.roundtrip_latency_ms ? `${health.roundtrip_latency_ms} ms` : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
