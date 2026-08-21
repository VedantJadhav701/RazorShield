# RazorShield API Contract & Integration Reference

This document defines the official Gradio API contract exposed by the Hugging Face Space backend (`vedantjadhav701/razorshield-api`) for integration with the Vercel Next.js frontend.

---

## 1. Overview

The backend exposes 5 logical API operations via Gradio HTTP / Client routes:

| Operation | Gradio `api_name` | Primary Function |
| :--- | :--- | :--- |
| **`analyze_transaction`** | `"analyze_transaction"` | Real-time transaction fraud & merchant incident risk analysis |
| **`analyze_merchant`** | `"analyze_merchant"` | Query live merchant temporal rolling state & active campaign info |
| **`run_scenario`** | `"run_scenario"` | Chronologically replay test scenarios for interactive demo |
| **`explain_evidence`** | `"explain_evidence"` | Direct structured evidence to zero-shot SLM explanation conversion |
| **`reset_demo_state`** | `"reset_demo_state"` | Reset all merchant temporal state, incident counters, & campaigns |

---

## 2. API Endpoint Specification

### Endpoint 1: `analyze_transaction`

Evaluates transaction fraud probability, merchant rolling temporal state, deployable spike model, persistent incident detection, and outputs grounded SLM explanations for elevated risk levels.

#### Request Inputs (Ordered Arguments for Gradio Client)

| Argument Index | Parameter | Type | Required | Default | Description |
| :---: | :--- | :--- | :---: | :--- | :--- |
| `0` | `merchant_id` | `str` | Yes | `"M_101"` | Unique merchant identifier |
| `1` | `transaction_id` | `str` | Yes | `"TX_994182"` | Unique transaction identifier |
| `2` | `customer_id` | `str` | No | `"C_1048"` | Customer identifier |
| `3` | `device_id` | `str` | No | `"D_882"` | Device identifier |
| `4` | `event_time` | `str` | Yes | `ISO timestamp` | Timestamp (e.g. `"2026-08-22T01:30:00"`) |
| `5` | `amount` | `float` | Yes | `125.50` | Transaction amount in USD |
| `6` | `payment_method` | `str` | No | `"card"` | `"card"`, `"ach"`, `"crypto"`, `"paypal"` |
| `7` | `transaction_type` | `str` | No | `"sale"` | `"sale"`, `"transfer"`, `"refund"` |
| `8` | `policy_mode` | `str` | No | `"BALANCED"` | `"CONSERVATIVE"`, `"BALANCED"`, `"HIGH_SENSITIVITY"` |

#### Response Schema (`AnalyzeTransactionResponse`)

```json
{
  "transaction_id": "TX_994182",
  "merchant_id": "M_101",
  "transaction_risk": {
    "fraud_probability": 0.8124
  },
  "merchant_risk": {
    "spike_probability": 0.8841,
    "fraud_excess_ratio": 8.24,
    "velocity_ratio": 4.10,
    "incident_state": "ALERT",
    "severity": "HIGH",
    "incident_score": 0.8483,
    "suspicious_windows": 3
  },
  "campaign": {
    "active": true,
    "campaign_name": "PROMOTIONAL_SALE"
  },
  "decision": {
    "action": "ALERT",
    "policy_mode": "BALANCED"
  },
  "explanation": {
    "title": "RazorShield Defensive Risk Assessment: ALERT (HIGH Severity)",
    "summary": "RazorShield classified merchant M_101 activity as ALERT (HIGH severity) because a fraud anomaly persisted across 3 consecutive monitoring windows. Estimated fraud excess ratio is 8.2x baseline with volume velocity 4.1x baseline.",
    "key_signals": [
      "Policy Incident Score: 0.85",
      "Fraud Excess Ratio: 8.2x baseline",
      "Volume Velocity Ratio: 4.1x baseline",
      "Consecutive Suspicious Windows: 3"
    ],
    "campaign_context": "A promotional campaign is currently active for merchant M_101. Volume velocity (4.1x baseline) is normalized, but fraud excess (8.2x baseline) remains actionable.",
    "recommended_action": "Initiate immediate merchant review, enforce step-up authentication, and review high-risk transaction batches.",
    "confidence_note": "Decision (ALERT) is authoritatively determined by RazorShield policy engine."
  },
  "performance": {
    "risk_engine_latency_ms": 0.619,
    "slm_latency_ms": 472.03,
    "total_latency_ms": 472.65
  }
}
```

---

### Endpoint 2: `analyze_merchant`

#### Request Input: `merchant_id` (str)
#### Response:
```json
{
  "merchant_id": "M_101",
  "rolling_window": {
    "rolling_txn_count_15m": 45,
    "baseline_txn_count_15m": 10,
    "velocity_ratio": 4.5,
    "estimated_fraud_count": 0.85,
    "expected_fraud_count": 0.10,
    "fraud_excess_ratio": 8.5
  },
  "incident_state": {
    "merchant_id": "M_101",
    "current_spike_probability": 0.88,
    "current_fraud_excess_ratio": 8.5,
    "current_velocity_ratio": 4.5,
    "suspicious_transaction_count": 3,
    "consecutive_suspicious_windows": 3,
    "campaign_active": true
  }
}
```

---

### Endpoint 3: `run_scenario`

#### Request Inputs: `scenario_name` (str), `policy_mode` (str)
- Options: `"NORMAL"`, `"VOLUME_ONLY_SPIKE"`, `"AMOUNT_SHIFT"`, `"FRAUD_SPIKE"`, `"FRAUD_DURING_FLASH_SALE"`

---

### Endpoint 4: `explain_evidence`

#### Request Input: `evidence_json` (str)
Converts raw evidence JSON into grounded SLM output with validation report.

---

### Endpoint 5: `reset_demo_state`

#### Request Input: None
#### Response:
```json
{
  "status": "SUCCESS",
  "message": "All merchant states and campaigns reset."
}
```

---

## 3. Vercel / Client Integration Code Snippet (JS / TS)

```typescript
import { client } from "@gradio/client";

const spaceUrl = "vedantjadhav701/razorshield-api";

export async function analyzeTransaction(payload: any) {
  const app = await client(spaceUrl);
  const result = await app.predict("analyze_transaction", [
    payload.merchant_id,
    payload.transaction_id,
    payload.customer_id || "C_UNKNOWN",
    payload.device_id || "D_UNKNOWN",
    payload.event_time,
    payload.amount,
    payload.payment_method || "card",
    payload.transaction_type || "sale",
    payload.policy_mode || "BALANCED"
  ]);
  return JSON.parse(result.data[0]);
}
```
