"use client";

import React, { useState } from "react";
import { MessageSquare, Send, X, Bot, Loader2, Sparkles } from "lucide-react";
import { AnalyzeTransactionResponse } from "@/lib/types";
import { explainEvidencePayload } from "@/lib/api";

interface Props {
  data: AnalyzeTransactionResponse | null;
}

interface ChatMessage {
  id: string;
  sender: "user" | "slm";
  text: string;
  timestamp: string;
  latencyMs?: number;
}

export default function SLMChatDrawer({ data }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init",
      sender: "slm",
      text: "Hello! I am RAZOR, your RazorShield AI Risk Assistant powered by Qwen2.5-0.5B. Ask me anything about the active transaction evaluation, merchant evidence signals, or policy decision.",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);

  const quickPrompts = [
    "Explain the decision for this transaction.",
    "What are the primary risk drivers?",
    "Should an analyst flag this merchant?",
    "How does flash sale campaign normalization work?",
  ];

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    const start = performance.now();

    try {
      // Build complete, valid EvidenceInput object for Pydantic schema
      const evidenceContext = {
        merchant_id: data?.merchant_id || "M_101",
        incident_state: data?.merchant_risk?.incident_state || "NORMAL",
        severity: data?.merchant_risk?.severity || "LOW",
        incident_score: data?.merchant_risk?.incident_score ?? 0.05,
        spike_probability: data?.merchant_risk?.spike_probability ?? 0.0,
        fraud_excess_ratio: data?.merchant_risk?.fraud_excess_ratio ?? 1.0,
        velocity_ratio: data?.merchant_risk?.velocity_ratio ?? 1.0,
        suspicious_windows: data?.merchant_risk?.suspicious_windows ?? 0,
        total_suspicious_windows: data?.merchant_risk?.suspicious_windows ?? 0,
        campaign_active: Boolean(data?.campaign?.active),
        policy_mode: data?.decision?.policy_mode || "BALANCED",
        recommended_action: data?.decision?.action || "APPROVE",
        signals: [
          {
            name: "fraud_excess_ratio",
            value: data?.merchant_risk?.fraud_excess_ratio ?? 1.0,
            direction: (data?.merchant_risk?.fraud_excess_ratio ?? 1.0) > 1.5 ? "elevated" : "normal",
          },
          {
            name: "velocity_ratio",
            value: data?.merchant_risk?.velocity_ratio ?? 1.0,
            direction: (data?.merchant_risk?.velocity_ratio ?? 1.0) > 2.0 ? "elevated" : "normal",
          },
        ],
      };

      const res = await explainEvidencePayload(JSON.stringify(evidenceContext));
      const latency = Math.round(performance.now() - start);

      const expObj = res?.explanation || (res?.title ? res : null);
      let replyText = "";

      if (expObj && expObj.summary) {
        replyText = expObj.summary;
        if (expObj.recommended_action) {
          replyText += `\n\n📌 Recommended Action: ${expObj.recommended_action}`;
        }
        if (expObj.key_signals && Array.isArray(expObj.key_signals) && expObj.key_signals.length > 0) {
          replyText += `\n\n🔑 Key Signals:\n• ` + expObj.key_signals.join("\n• ");
        }
      } else if (typeof res === "string") {
        replyText = res;
      } else if (res?.error) {
        replyText = `Error: ${res.error}${res.details ? ` (${res.details})` : ""}`;
      } else {
        replyText =
          typeof res === "object"
            ? JSON.stringify(res, null, 2)
            : "RAZOR assistant evaluated the structured risk evidence.";
      }

      const slmMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "slm",
        text: replyText,
        timestamp: new Date().toLocaleTimeString(),
        latencyMs: latency,
      };

      setMessages((prev) => [...prev, slmMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "slm",
        text: `Error reaching RAZOR assistant: ${err.message || "Request failed"}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Co-Pilot Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 bg-brand-red hover:bg-brand-red-hover text-white px-4 py-3 font-mono text-xs uppercase font-bold flex items-center space-x-2 shadow-2xl z-50 transition-transform active:scale-95 rounded-none"
      >
        <Bot className="w-4 h-4" />
        <span>RAZOR AI ASSISTANT</span>
        <Sparkles className="w-3.5 h-3.5 fill-white text-white animate-pulse" />
      </button>

      {/* Slide-out Assistant Drawer */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 w-full sm:w-[440px] bg-brand-black border-l border-brand-border z-50 flex flex-col justify-between shadow-2xl">
          {/* Header */}
          <div className="p-4 border-b border-brand-border/60 bg-brand-dark flex items-center justify-between font-mono text-xs">
            <div className="flex items-center space-x-2 text-brand-red font-bold uppercase">
              <Bot className="w-4 h-4" />
              <span>RAZOR AI ASSISTANT</span>
            </div>

            <div className="flex items-center space-x-3 text-brand-muted">
              <span className="text-[10px] border border-brand-border px-2 py-0.5 text-emerald-400">
                Qwen2.5-0.5B
              </span>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Active Context Banner */}
          <div className="bg-brand-dark/60 border-b border-brand-border/40 p-3 font-mono text-[11px] flex items-center justify-between text-brand-muted">
            <span>
              CONTEXT:{" "}
              <strong className="text-white">
                {data ? `${data.merchant_id} / ${data.transaction_id}` : "DEFAULT CONTEXT (M_101)"}
              </strong>
            </span>
            {data && (
              <span className="text-emerald-400 font-bold uppercase">
                {data.decision.action}
              </span>
            )}
          </div>

          {/* Messages Stream */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 font-mono text-xs">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col space-y-1 ${
                  msg.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div className="flex items-center space-x-2 text-[10px] text-brand-muted">
                  <span>{msg.sender === "user" ? "ANALYST" : "RAZOR ASSISTANT"}</span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {msg.latencyMs && (
                    <span className="text-emerald-400">({msg.latencyMs} ms)</span>
                  )}
                </div>

                <div
                  className={`p-3 max-w-[88%] text-[11px] leading-relaxed border whitespace-pre-wrap ${
                    msg.sender === "user"
                      ? "bg-brand-red/10 border-brand-red/40 text-white"
                      : "bg-brand-dark border-brand-border/60 text-brand-muted"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center space-x-2 font-mono text-[11px] text-brand-red animate-pulse p-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>RAZOR assistant evaluating structured evidence...</span>
              </div>
            )}
          </div>

          {/* Quick Prompts & Input Area */}
          <div className="p-4 border-t border-brand-border/60 bg-brand-dark space-y-3">
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-brand-muted uppercase font-bold block">
                Quick Analyst Queries:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {quickPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="text-[10px] font-mono bg-brand-black border border-brand-border hover:border-brand-red text-brand-muted hover:text-white px-2 py-1 transition-colors text-left"
                  >
                    💬 {prompt}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask RAZOR assistant about risk context..."
                className="flex-1 bg-brand-black border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
              />
              <button
                onClick={() => handleSend()}
                disabled={isLoading || !inputQuery.trim()}
                className="bg-brand-red hover:bg-brand-red-hover disabled:bg-brand-border text-white px-3 py-2 transition-colors rounded-none"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
