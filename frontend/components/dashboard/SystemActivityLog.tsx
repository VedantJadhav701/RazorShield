"use client";

import React from "react";
import { LogEventItem } from "@/lib/types";
import { Activity } from "lucide-react";

interface Props {
  logs: LogEventItem[];
}

export default function SystemActivityLog({ logs }: Props) {
  return (
    <div className="bg-background border border-border p-6 font-mono text-xs space-y-4 rounded-xl shadow-sm">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center space-x-2 text-accent font-bold uppercase tracking-widest">
          <Activity className="w-4 h-4" />
          <span>SYSTEM ACTIVITY LOG (LIVE TRACE)</span>
        </div>
        <span className="text-[10px] text-muted-foreground uppercase">
          Real Backend Request Lifecycle
        </span>
      </div>

      {logs.length === 0 ? (
        <div className="text-muted-foreground text-[11px] py-4 text-center">
          No requests recorded in current session. Submit a transaction or scenario to trace execution.
        </div>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`p-2.5 rounded-lg border text-[11px] flex items-center justify-between ${
                log.is_error
                  ? "bg-rose-50 border-rose-200 text-rose-700 font-semibold"
                  : "bg-secondary/40 border-border text-foreground"
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="text-foreground font-semibold">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-accent uppercase font-bold">
                  [{log.event_type}]
                </span>
                <span className="text-foreground font-medium">{log.summary}</span>
              </div>

              {log.latency_ms !== undefined && (
                <span className="text-emerald-600 font-bold">
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
