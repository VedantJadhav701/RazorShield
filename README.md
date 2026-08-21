---
title: RazorShield AI Risk Engine & SLM Explanation API
emoji: 🛡️
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 5.14.0
app_file: app.py
pinned: false
license: mit
short_description: Real-time fraud detection & ZeroGPU SLM explanations.
---

# RazorShield — AI-Powered Merchant Fraud & Risk Intelligence

RazorShield is an enterprise-grade, multi-layered merchant fraud detection and risk intelligence engine combining calibrated machine learning models, rolling temporal merchant state, campaign-aware incident detection, and zero-shot Small Language Model (SLM) explanations powered by **ZeroGPU**.

---

## 🌐 Live System Endpoints

- **Live Next.js Frontend (Vercel)**: [https://razorshield.vercel.app](https://razorshield.vercel.app)
- **Hugging Face Space Backend**: [https://huggingface.co/spaces/vedantjadhav701/razorshield-api](https://huggingface.co/spaces/vedantjadhav701/razorshield-api)
- **Direct API Endpoint**: `https://vedantjadhav701-razorshield-api.hf.space`
- **GitHub Repository**: [https://github.com/VedantJadhav701/RazorShield](https://github.com/VedantJadhav701/RazorShield)

---

## 🎬 How to Demo (3–5 Minute Judge Walkthrough)

1. **Landing Stage (`/`)**: Start on the cinematic fullscreen stage highlighting *"Fraud detection without false alarms."* Click **LAUNCH RAZORSHIELD** to enter the console.
2. **Risk Console (`/dashboard`)**: Submit a real-time transaction to view sub-millisecond risk decisioning (`DETERMINISTIC RISK ENGINE`) alongside structured evidence and AI-generated explanations (`Qwen2.5-0.5B-Instruct`).
3. **Hard-Negative Isolation (`/scenarios`)**: Select **FLASH SALE (VOLUME SURGE)**. Click **RUN SCENARIO REPLAY**. Observe that despite a 4.0x volume surge, fraud excess remains 1.0x, resulting in **`NORMAL`** decision (0% false alert).
4. **Persistent Fraud Attack (`/scenarios`)**: Select **FLASH SALE WITH FRAUD ATTACK**. Click **RUN SCENARIO REPLAY**. Observe that campaign state is recognized, but persistent fraud excess triggers an authoritative **`ALERT`** after $N=2$ windows with grounded SLM explanations.
5. **Empirical Benchmarks (`/evaluation`)**: Open the Evaluation tab to inspect verified test-set metrics (88.89% scenario recall, 0.00% flash sale false alerts, 100% SLM grounding).

---

## 🏗️ System Architecture

```
Incoming Transaction Event
       │
       ▼
1. Calibrated Transaction Model (Isotonic XGBoost - P_fraud)
       │
       ▼
2. Merchant Temporal State Manager (15m Rolling Windows)
       │
       ▼
3. Deployable Fraud-Spike Detector (14 Deployable Features - P_spike)
       │
       ▼
4. Merchant Incident Engine (Persistence N=2 Windows)
       │
       ▼
5. Decision Routing (APPROVE / VERIFY / ALERT)
       │
       ▼
6. ZeroGPU SLM Explanation Layer (Qwen/Qwen2.5-0.5B-Instruct + Grounding Validator)
```

> [!IMPORTANT]
> **Core Architectural Principle**: The RazorShield ML and policy engines are **deterministic and authoritative**. The Hugging Face SLM is strictly an **evidence-to-language explanation layer**. The SLM **NEVER** determines fraud, modifies risk decisions, generates risk scores, overrides severity, or invents evidence.

---

## 📊 Key Performance Benchmarks

### 1. Risk Engine Benchmarks
- **Transaction Fraud Model ECE**: `0.188%` (Isotonic calibrated test set Expected Calibration Error)
- **Deterministic Decision Latency**: **`0.619 ms`** average latency (Sub-millisecond real-time stream processing)
- **False Alert Rates across Demo Scenarios**:
  - `normal`: **`0.00%`** false alerts
  - `volume_only_spike` (Flash Sale): **`0.00%`** false alerts
  - `amount_shift` (Bulk Order Shift): **`0.00%`** false alerts
- **Scenario Fraud Spike Incident Recall**: **`88.89%`**

### 2. ZeroGPU SLM Explanation Layer Benchmarks (Qwen2.5-0.5B-Instruct)
- **Benchmark Size**: `300` deterministic evidence examples
- **JSON Validity**: **`100.0%`**
- **Numeric Grounding**: **`100.0%`**
- **Decision & Severity Consistency**: **`100.0%`**
- **Measured Hallucination Rate**: **`0.00%`** (0% measured hallucination under benchmark dataset)
- **Average GPU Latency**: **`472.03 ms`** (P95: `501.07 ms`)
- **VRAM Memory Usage**: **`943.91 MB`**

---

## ⚡ ZeroGPU Resource Efficiency

CPU handles request validation, XGBoost inference, rolling merchant state, incident policy evaluation, and grounding validation. **ZeroGPU is reserved exclusively for the SLM generation function** (`@spaces.GPU`), ensuring minimal VRAM allocation and rapid response times.

---

## 🔌 Public API Endpoints

The backend exposes Gradio API endpoints for external frontend integration:

- `analyze_transaction`: Real-time transaction fraud & merchant incident risk assessment
- `analyze_merchant`: Query live merchant temporal rolling state & active campaign info
- `run_scenario`: Chronologically replay test scenarios for interactive demo
- `explain_evidence`: Direct structured evidence to zero-shot SLM explanation conversion
- `reset_demo_state`: Reset all merchant temporal state, incident counters, & campaigns

For full documentation, see [docs/API_CONTRACT.md](docs/API_CONTRACT.md).
