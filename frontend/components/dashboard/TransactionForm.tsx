"use client";

import React, { useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import { TransactionApiInput } from "@/lib/types";

interface Props {
  onSubmit: (input: TransactionApiInput) => void;
  isLoading: boolean;
}

export default function TransactionForm({ onSubmit, isLoading }: Props) {
  const [merchantId, setMerchantId] = useState("M_101");
  const [transactionId, setTransactionId] = useState("TX_994182");
  const [customerId, setCustomerId] = useState("C_1048");
  const [deviceId, setDeviceId] = useState("D_882");
  const [amount, setAmount] = useState<number>(125.50);
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [transactionType, setTransactionType] = useState("sale");
  const [policyMode, setPolicyMode] = useState<"CONSERVATIVE" | "BALANCED" | "HIGH_SENSITIVITY">("BALANCED");

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
    <form onSubmit={handleSubmit} className="bg-brand-black border border-brand-border p-6 space-y-4">
      <div className="font-mono text-xs text-brand-red tracking-widest uppercase mb-2">
        // SUBMIT TRANSACTION PAYLOAD
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="font-mono text-[11px] text-brand-muted uppercase block mb-1">
            Merchant ID
          </label>
          <input
            type="text"
            value={merchantId}
            onChange={(e) => setMerchantId(e.target.value)}
            className="w-full bg-brand-dark border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
            required
          />
        </div>

        <div>
          <label className="font-mono text-[11px] text-brand-muted uppercase block mb-1">
            Transaction ID
          </label>
          <input
            type="text"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="w-full bg-brand-dark border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
            required
          />
        </div>

        <div>
          <label className="font-mono text-[11px] text-brand-muted uppercase block mb-1">
            Customer ID
          </label>
          <input
            type="text"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="w-full bg-brand-dark border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
          />
        </div>

        <div>
          <label className="font-mono text-[11px] text-brand-muted uppercase block mb-1">
            Device ID
          </label>
          <input
            type="text"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            className="w-full bg-brand-dark border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
          />
        </div>

        <div>
          <label className="font-mono text-[11px] text-brand-muted uppercase block mb-1">
            Amount ($)
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
            className="w-full bg-brand-dark border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
            required
          />
        </div>

        <div>
          <label className="font-mono text-[11px] text-brand-muted uppercase block mb-1">
            Policy Mode
          </label>
          <select
            value={policyMode}
            onChange={(e) => setPolicyMode(e.target.value as any)}
            className="w-full bg-brand-dark border border-brand-border text-white px-3 py-2 font-mono text-xs focus:outline-none focus:border-brand-red"
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
        className="w-full bg-brand-red hover:bg-brand-red-hover disabled:bg-brand-border text-white font-mono text-xs tracking-widest uppercase py-3 flex items-center justify-center space-x-2 transition-colors rounded-none mt-4"
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
