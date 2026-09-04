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
short_description: Real-time fraud detection & NVIDIA GPT-5 SLM explanations.
---

# 🛡️ RazorShield — AI Merchant Risk & Fraud Intelligence Engine

RazorShield is an enterprise-grade, multi-layered merchant fraud detection and risk intelligence platform. It combines calibrated machine learning models, rolling temporal merchant state, campaign-aware incident detection, and zero-shot Small Language Model (SLM) explanations powered by **NVIDIA Build API (`openai/gpt-oss-20b` / GPT-5 class SLM)** and Hugging Face ZeroGPU.

---

## 🌐 Live System Endpoints & Repositories

- **Live Production Frontend (Vercel)**: [https://razorshield.vercel.app](https://razorshield.vercel.app)
- **Live Scenarios Engine**: [https://razorshield.vercel.app/scenarios](https://razorshield.vercel.app/scenarios)
- **Hugging Face Space Backend**: [https://huggingface.co/spaces/vedantjadhav701/razorshield-api](https://huggingface.co/spaces/vedantjadhav701/razorshield-api)
- **Direct Backend API Endpoint**: `https://vedantjadhav701-razorshield-api.hf.space`
- **GitHub Repository**: [https://github.com/VedantJadhav701/RazorShield](https://github.com/VedantJadhav701/RazorShield)

---

## ✨ Highlights & Key Innovations

* **Smarter Risk Protection**: Decouples volume velocity surges (e.g., flash sales and promotional spikes) from actual excess fraud signals, preventing hard-negative false alerts.
* **Modern Light-Theme SaaS UI**: Designed with Google Fonts (*Instrument Serif* + *Inter*), CloudFront video hero atmosphere, custom-coded interactive React dashboard preview, smooth cubic Bézier charts, and quick-test sample presets (`Normal Retail`, `Amount Anomaly`, `Fraud Burst`, `Flash Sale Promo`).
* **Authoritative Deterministic Risk Engine**: XGBoost model with Isotonic Calibration ($ECE = 0.188\%$) delivering **sub-millisecond (< 0.62 ms)** transaction scoring.
* **Temporal Merchant State Manager**: 15-minute rolling window tracking volume velocity ratios, fraud excess ratios, and incident persistence ($N=2$ anomaly windows).
* **NVIDIA Build API / GPT-5 SLM Explainer**: Zero-shot natural language explanation layer with strict JSON schema parsing, regex fallback repair, and 100% numeric evidence grounding (0% measured hallucination).
* **Interactive Scenario Replay**: Replays 2,900+ real transaction streams chronologically across 5 distinct scenario types in **< 4.3 seconds**.

---

## 🎬 Quick Judge & Demo Walkthrough (3–5 Minutes)

1. **Landing Stage (`/`)**: Experience the cinematic SaaS hero section highlighting *"The Future of Smarter Risk Protection"*. Click **Launch Operations Console** to open the risk engine.
2. **Operations Console (`/dashboard`)**: Click any **Quick Test Sample** chip (`Normal Retail`, `Amount Anomaly`, `Fraud Burst`, `Flash Sale Promo`) or submit custom transactions. View real-time sub-millisecond risk decisioning (`DETERMINISTIC RISK ENGINE`) alongside structured evidence and NVIDIA SLM explanations.
3. **Interactive AI Assistant (`/dashboard`)**: Click **RAZOR AI ASSISTANT** on the bottom right to interact with the SLM co-pilot for on-demand context analysis.
4. **Hard-Negative Isolation (`/scenarios`)**: Select **FLASH SALE (VOLUME SURGE)** and click **RUN SCENARIO REPLAY**. Observe that despite a 4.0x volume surge, fraud excess remains 1.0x, yielding a **`NORMAL`** decision (0% false alert).
5. **Persistent Fraud Attack (`/scenarios`)**: Select **FLASH SALE WITH FRAUD ATTACK** and click **RUN SCENARIO REPLAY**. Observe that campaign state is recognized, but persistent fraud excess triggers an authoritative **`ALERT`** after $N=2$ windows with grounded SLM explanations.
6. **Empirical Benchmarks (`/evaluation`)**: Open the Evaluation tab to inspect verified test-set metrics (88.89% scenario recall, 0.00% flash sale false alerts, 100% SLM grounding).

---

## 🏗️ System Architecture

```
Incoming Transaction Event Payload
       │
       ▼
1. Calibrated Transaction Model (Isotonic Calibrated XGBoost -> P_fraud)
       │
       ▼
2. Merchant Temporal State Manager (15-Minute Rolling Windows)
       │
       ▼
3. Deployable Fraud-Spike Detector (14 Temporal Features -> P_spike)
       │
       ▼
4. Merchant Incident Engine (Persistence N=2 Anomaly Windows)
       │
       ▼
5. Authoritative Decision Routing (APPROVE / VERIFY / ALERT)
       │
       ▼
6. SLM Explanation Layer (NVIDIA Build API / openai/gpt-oss-20b + Grounding Validator)
```

> [!IMPORTANT]
> **Core Architectural Guarantee**: The RazorShield ML model and policy engines are **100% deterministic and authoritative**. The NVIDIA SLM operates strictly as an **evidence-to-language explanation layer**. The SLM **NEVER** determines fraud, modifies risk decisions, generates risk scores, overrides severity, or invents ungrounded evidence.

---

## 📊 Key Performance Benchmarks

### 1. Risk Engine Metrics
- **Transaction Fraud Model ECE**: `0.188%` (Isotonic calibrated test set Expected Calibration Error)
- **Deterministic Decision Latency**: **`0.619 ms`** average latency (Sub-millisecond stream processing)
- **False Alert Rates across Scenarios**:
  - `normal`: **`0.00%`** false alerts
  - `volume_only_spike` (Flash Sale): **`0.00%`** false alerts
  - `amount_shift` (Bulk Order Shift): **`0.00%`** false alerts
- **Scenario Fraud Spike Incident Recall**: **`88.89%`**

### 2. SLM Explanation Layer Metrics (NVIDIA Build API `openai/gpt-oss-20b`)
- **Benchmark Evaluation Size**: `300` deterministic evidence samples
- **JSON Format Validity**: **`100.0%`**
- **Numeric Evidence Grounding**: **`100.0%`**
- **Decision & Severity Consistency**: **`100.0%`**
- **Measured Hallucination Rate**: **`0.00%`**
- **Average API Response Latency**: **`~240 ms`** (Sub-second explanation delivery)

---

## 🔌 API Endpoints & Contract

The backend exposes Gradio 5+ API endpoints (`/gradio_api/call/...`) mirrored by serverless Next.js API routes (`/api/...`):

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check & backend connectivity probe |
| `/api/transaction` | `POST` | Real-time transaction fraud & merchant incident risk evaluation |
| `/api/merchant` | `POST` | Query live merchant temporal state & campaign information |
| `/api/scenario` | `POST` | Replay 600-transaction scenario stream chronologically |
| `/api/explain` | `POST` | Convert structured evidence into grounded SLM explanation |
| `/api/reset` | `POST` | Reset temporal merchant states, incident counters, & campaigns |

---

## 🧪 Test Suite & Verification

RazorShield includes full end-to-end pytest and Next.js type verification:

* **Backend Unit & Integration Tests**: `59 passed` in `pytest` suite.
* **Next.js Production Build**: `13/13 pages` compiled successfully with zero type or lint errors.

```bash
# Run backend test suite
pytest

# Run frontend build
cd frontend && npm run build
```

---

## 📄 License

Distributed under the **MIT License**.
