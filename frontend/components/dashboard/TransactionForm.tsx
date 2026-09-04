"use client";

import React, { useState } from "react";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { TransactionApiInput } from "@/lib/types";

interface Props {
  onSubmit: (input: TransactionApiInput) => void;
  isLoading: boolean;
}

interface Preset {
  id: string;
  label: string;
  desc: string;
  badge: string;
  badgeColor: string;
  data: {
    merchantId: string;
    transactionId: string;
    customerId: string;
    deviceId: string;
    amount: number;
    paymentMethod: string;
    transactionType: string;
    policyMode: "CONSERVATIVE" | "BALANCED" | "HIGH_SENSITIVITY";
  };
}

const SAMPLE_PRESETS: Preset[] = [
  {
    id: "normal",
    label: "Normal Retail",
    desc: "$45.50 card sale",
    badge: "LOW RISK",
    badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
    data: {
      merchantId: "M_101",
      transactionId: "TX_100001",
      customerId: "C_1048",
      deviceId: "D_882",
      amount: 45.50,
      paymentMethod: "card",
      transactionType: "sale",
      policyMode: "BALANCED",
    },
  },
  {
    id: "anomaly",
    label: "Amount Anomaly",
    desc: "$4,850 ACH transfer",
    badge: "ELEVATED",
    badgeColor: "bg-amber-50 text-amber-700 border-amber-200",
    data: {
      merchantId: "M_102",
      transactionId: "TX_100002",
      customerId: "C_9999",
      deviceId: "D_999",
      amount: 4850.00,
      paymentMethod: "ach",
      transactionType: "transfer",
      policyMode: "BALANCED",
    },
  },
  {
    id: "fraud",
    label: "Fraud Burst",
    desc: "$950 crypto refund",
    badge: "HIGH RISK",
    badgeColor: "bg-rose-50 text-rose-700 border-rose-200",
    data: {
      merchantId: "M_103",
      transactionId: "TX_100003",
      customerId: "C_8812",
      deviceId: "D_551",
      amount: 950.00,
      paymentMethod: "crypto",
      transactionType: "refund",
      policyMode: "HIGH_SENSITIVITY",
    },
  },
  {
    id: "flash_sale",
    label: "Flash Sale Promo",
    desc: "$29.99 promo order",
    badge: "HARD NEGATIVE",
    badgeColor: "bg-indigo-50 text-indigo-700 border-indigo-200",
    data: {
      merchantId: "M_104",
      transactionId: "TX_100004",
      customerId: "C_2201",
      deviceId: "D_330",
      amount: 29.99,
      paymentMethod: "card",
      transactionType: "sale",
      policyMode: "CONSERVATIVE",
    },
  },
];

export default function TransactionForm({ onSubmit, isLoading }: Props) {
  const [activePreset, setActivePreset] = useState<string>("normal");
  const [merchantId, setMerchantId] = useState("M_101");
  const [transactionId, setTransactionId] = useState("TX_100001");
  const [customerId, setCustomerId] = useState("C_1048");
  const [deviceId, setDeviceId] = useState("D_882");
  const [amount, setAmount] = useState<number>(45.50);
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [transactionType, setTransactionType] = useState("sale");
  const [policyMode, setPolicyMode] = useState<"CONSERVATIVE" | "BALANCED" | "HIGH_SENSITIVITY">("BALANCED");

  const loadPreset = (preset: Preset) => {
    setActivePreset(preset.id);
    setMerchantId(preset.data.merchantId);
    setTransactionId(preset.data.transactionId);
    setCustomerId(preset.data.customerId);
    setDeviceId(preset.data.deviceId);
    setAmount(preset.data.amount);
    setPaymentMethod(preset.data.paymentMethod);
    setTransactionType(preset.data.transactionType);
    setPolicyMode(preset.data.policyMode);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      merchant_id: merchantId,
      transaction_id: transactionId,
      customer_id: customerId,
      device_id: deviceId,
      event_time: new Date().toISOString(),
      amount: Number(amount),
      payment_method: paymentMethod,
      transaction_type: transactionType,
      policy_mode: policyMode,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-background border border-border p-6 space-y-4 rounded-xl shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="font-mono text-xs text-accent tracking-widest uppercase font-semibold">
          // SUBMIT TRANSACTION PAYLOAD
        </div>
        <div className="flex items-center space-x-1 text-[11px] font-body text-muted-foreground">
          <Sparkles className="w-3 h-3 text-amber-500" />
          <span>QUICK TEST SAMPLES</span>
        </div>
      </div>

      {/* Quick Test Samples Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pb-3 border-b border-border">
        {SAMPLE_PRESETS.map((preset) => {
          const isSelected = activePreset === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              onClick={() => loadPreset(preset)}
              className={`p-2.5 text-left border rounded-lg transition-all ${
                isSelected
                  ? "bg-secondary border-accent text-foreground shadow-sm font-medium"
                  : "bg-background border-border hover:border-accent/40 text-muted-foreground hover:text-foreground"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-body font-bold text-xs truncate">{preset.label}</span>
                <span className={`text-[9px] font-mono px-1.5 py-0.5 border rounded ${preset.badgeColor}`}>
                  {preset.badge}
                </span>
              </div>
              <p className="font-mono text-[10px] opacity-75 truncate">{preset.desc}</p>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-body">
        <div>
          <label className="text-[11px] font-medium text-muted-foreground uppercase block mb-1">
            Merchant ID
          </label>
          <input
            type="text"
            value={merchantId}
            onChange={(e) => setMerchantId(e.target.value)}
            className="w-full bg-secondary/40 border border-border text-foreground rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent"
            required
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground uppercase block mb-1">
            Transaction ID
          </label>
          <input
            type="text"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="w-full bg-secondary/40 border border-border text-foreground rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent"
            required
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground uppercase block mb-1">
            Customer ID
          </label>
          <input
            type="text"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="w-full bg-secondary/40 border border-border text-foreground rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent"
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground uppercase block mb-1">
            Device ID
          </label>
          <input
            type="text"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            className="w-full bg-secondary/40 border border-border text-foreground rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent"
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground uppercase block mb-1">
            Amount ($)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
            className="w-full bg-secondary/40 border border-border text-foreground rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent"
            required
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground uppercase block mb-1">
            Policy Mode
          </label>
          <select
            value={policyMode}
            onChange={(e) => setPolicyMode(e.target.value as any)}
            className="w-full bg-secondary/40 border border-border text-foreground rounded-md px-3 py-2 text-xs focus:outline-none focus:border-accent"
          >
            <option value="CONSERVATIVE">CONSERVATIVE</option>
            <option value="BALANCED">BALANCED</option>
            <option value="HIGH_SENSITIVITY">HIGH_SENSITIVITY</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-primary hover:bg-primary/90 disabled:bg-muted text-primary-foreground font-body text-xs font-medium uppercase tracking-wider py-3 flex items-center justify-center space-x-2 transition-all rounded-md shadow-sm mt-4"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>ANALYZING TRANSACTION...</span>
          </>
        ) : (
          <>
            <span>EVALUATE TRANSACTION RISK</span>
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </form>
  );
}
