"use client";

import React, { useState, useRef } from "react";
import { Play, Square, Radio } from "lucide-react";
import { analyzeTransaction } from "@/lib/api";
import { AnalyzeTransactionResponse } from "@/lib/types";
import { formatFixed, formatPercent } from "@/lib/utils";

interface StreamItem {
  id: string;
  txId: string;
  merchantId: string;
  amount: number;
  action: string;
  fraudProb: number;
  latencyMs: number;
  timestamp: string;
}

interface Props {
  onTransactionAnalyzed: (res: AnalyzeTransactionResponse) => void;
}

export default function LiveStreamControls({ onTransactionAnalyzed }: Props) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamItems, setStreamItems] = useState<StreamItem[]>([]);
  const isStreamingRef = useRef(false);

  const samplePayloads = [
    { merchantId: "M_101", amount: 45.0, type: "NORMAL" },
    { merchantId: "M_101", amount: 120.0, type: "NORMAL" },
    { merchantId: "M_101", amount: 890.0, type: "ELEVATED" },
    { merchantId: "M_101", amount: 450.0, type: "NORMAL" },
    { merchantId: "M_101", amount: 1250.0, type: "ATTACK" },
  ];

  const startStream = async () => {
    if (isStreaming) return;
    setIsStreaming(true);
    isStreamingRef.current = true;

    for (let i = 0; i < samplePayloads.length; i++) {
      if (!isStreamingRef.current) break;
      const sample = samplePayloads[i];
      const txId = `STREAM_TX_${Date.now().toString().slice(-5)}`;

      try {
        const res = await analyzeTransaction({
          merchant_id: sample.merchantId,
          transaction_id: txId,
          amount: sample.amount,
          policy_mode: "BALANCED",
        });

        onTransactionAnalyzed(res);

        const item: StreamItem = {
          id: Math.random().toString(),
          txId: res.transaction_id,
          merchantId: res.merchant_id,
          amount: sample.amount,
          action: res.decision.action,
          fraudProb: res.transaction_risk.fraud_probability,
          latencyMs: res.meta?.roundtrip_latency_ms || 0,
          timestamp: new Date().toLocaleTimeString(),
        };

        setStreamItems((prev) => [item, ...prev].slice(0, 10));
      } catch (err) {
        console.error("Stream item error:", err);
      }

      // Delay between stream events
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }

    setIsStreaming(false);
    isStreamingRef.current = false;
  };

  const stopStream = () => {
    isStreamingRef.current = false;
    setIsStreaming(false);
  };

  return (
    <div className="bg-background border border-border p-6 font-body text-xs space-y-4 rounded-xl shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border pb-3">
        <div className="flex items-center space-x-2 text-accent font-bold uppercase tracking-widest font-mono">
          <Radio className={`w-4 h-4 ${isStreaming ? "animate-pulse text-accent" : ""}`} />
          <span>LIVE DEMO TRANSACTION STREAM</span>
        </div>

        <div>
          {!isStreaming ? (
            <button
              onClick={startStream}
              className="bg-primary hover:bg-primary/90 text-primary-foreground font-body text-xs font-medium px-4 py-2 uppercase tracking-wider flex items-center space-x-2 transition-all rounded-md shadow-sm"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>START DEMO STREAM</span>
            </button>
          ) : (
            <button
              onClick={stopStream}
              className="bg-secondary border border-rose-200 text-rose-700 hover:bg-rose-50 font-body text-xs px-4 py-2 uppercase font-bold flex items-center space-x-2 transition-all rounded-md"
            >
              <Square className="w-3.5 h-3.5 fill-rose-700" />
              <span>STOP STREAM</span>
            </button>
          )}
        </div>
      </div>

      {streamItems.length > 0 && (
        <div className="space-y-2 font-mono">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">
            Real Backend Stream Log (Live Response Stream)
          </div>
          <div className="space-y-1">
            {streamItems.map((item) => (
              <div
                key={item.id}
                className="bg-secondary/40 border border-border p-2.5 rounded-lg flex items-center justify-between text-[11px]"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-muted-foreground">{item.timestamp}</span>
                  <span className="text-foreground font-semibold">{item.txId}</span>
                  <span className="text-muted-foreground">${formatFixed(item.amount, 2)}</span>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-muted-foreground">P(fraud): {formatPercent(item.fraudProb)}</span>
                  <span
                    className={`font-bold uppercase px-2 py-0.5 border rounded-full ${
                      item.action === "ALERT"
                        ? "bg-rose-50 border-rose-200 text-rose-700"
                        : item.action === "VERIFY"
                        ? "bg-amber-50 border-amber-200 text-amber-700"
                        : "bg-emerald-50 border-emerald-200 text-emerald-700"
                    }`}
                  >
                    {item.action}
                  </span>
                  <span className="text-emerald-600 font-semibold">{item.latencyMs} ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
