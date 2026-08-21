"use client";

import React from "react";
import { LogEventItem } from "@/lib/types";
import { Activity } from "lucide-react";

interface Props {
  logs: LogEventItem[];
}

export default function SystemActivityLog({ logs }: Props) {
  return (
    <div className="bg-brand-black border border-brand-border p-6 font-mono text-xs space-y-4">
      <div className="flex items-center justify-between border-b border-brand-border/60 pb-3">
        <div className="flex items-center space-x-2 text-brand-red font-bold uppercase tracking-widest">
          <Activity className="w-4 h-4" />
          <span>SYSTEM ACTIVITY LOG (LIVE TRACE)</span>
        </div>
        <span className="text-[10px] text-brand-muted uppercase">
          Real Backend Request Lifecycle
        </span>
      </div>

      {logs.length === 0 ? (
        <div className="text-brand-muted text-[11px] py-4 text-center">
          No requests recorded in current session. Submit a transaction or scenario to trace execution.
        </div>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`p-2 border text-[11px] flex items-center justify-between ${
                log.is_error
                  ? "bg-brand-red/10 border-brand-red/40 text-brand-red"
                  : "bg-brand-dark border-brand-border/60 text-brand-muted"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-white font-semibold">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-brand-red uppercase font-bold">
                  [{log.event_type}]
                </span>
                <span className="text-white">{log.summary}</span>
              </div>

              {log.latency_ms !== undefined && (
                <span className="text-emerald-400 font-bold">
                  {log.latency_ms} ms
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
