"use client";

import React, { useState, useRef } from "react";
import { Play, Square, Loader2, Radio } from "lucide-react";
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
    <div className="bg-brand-black border border-brand-border p-6 font-mono text-xs space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-brand-border/60 pb-3">
        <div className="flex items-center space-x-2 text-brand-red font-bold uppercase tracking-widest">
          <Radio className={`w-4 h-4 ${isStreaming ? "animate-pulse text-brand-red" : ""}`} />
          <span>LIVE DEMO TRANSACTION STREAM</span>
        </div>

        <div>
          {!isStreaming ? (
            <button
              onClick={startStream}
              className="bg-brand-red hover:bg-brand-red-hover text-white font-mono text-xs px-4 py-2 uppercase font-bold flex items-center space-x-2 transition-colors rounded-none"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>START DEMO STREAM</span>
            </button>
          ) : (
            <button
              onClick={stopStream}
              className="bg-brand-dark border border-brand-red text-brand-red hover:bg-brand-red hover:text-white font-mono text-xs px-4 py-2 uppercase font-bold flex items-center space-x-2 transition-colors rounded-none"
            >
              <Square className="w-3.5 h-3.5 fill-brand-red hover:fill-white" />
              <span>STOP STREAM</span>
            </button>
          )}
        </div>
      </div>

      {streamItems.length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] text-brand-muted uppercase mb-1">
            Real Backend Stream Log (Live Response Stream)
          </div>
          <div className="space-y-1">
            {streamItems.map((item) => (
              <div
                key={item.id}
                className="bg-brand-dark border border-brand-border/60 p-2 flex items-center justify-between text-[11px]"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-brand-muted">{item.timestamp}</span>
                  <span className="text-white font-semibold">{item.txId}</span>
                  <span className="text-brand-muted">${formatFixed(item.amount, 2)}</span>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-brand-muted">P(fraud): {formatPercent(item.fraudProb)}</span>
                  <span
                    className={`font-bold uppercase px-2 py-0.5 border ${
                      item.action === "ALERT"
                        ? "bg-brand-red/10 border-brand-red/40 text-brand-red"
                        : item.action === "VERIFY"
                        ? "bg-amber-400/10 border-amber-400/40 text-amber-400"
                        : "bg-emerald-400/10 border-emerald-400/40 text-emerald-400"
                    }`}
                  >
                    {item.action}
                  </span>
                  <span className="text-emerald-400 font-semibold">{item.latencyMs} ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
