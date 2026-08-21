# RazorShield — Data Pipeline & Benchmark Documentation

This document describes the data preparation methodology, schemas, leakage-prevention guarantees, and reproduction steps for the **RazorShield** defensive AI fraud-spike detection benchmark.

---

## 1. Executive Summary & Datasets Overview

RazorShield generates and validates two distinct datasets:

| Dataset | Type | Primary Purpose | Source | Output Path |
| :--- | :--- | :--- | :--- | :--- |
| **Dataset A** | Model Dataset | Transaction-level fraud modeling ($P(\text{fraud} \mid \text{txn})$) | IEEE-CIS Fraud Detection (Kaggle) | `data/processed/dataset_a_model.parquet` |
| **Dataset B** | Evaluation / Hard Negative | Merchant-level temporal fraud-spike detection & scenario evaluation | Defensive Synthetic Pipeline (NVIDIA + NumPy) | `data/processed/dataset_b_scenarios.parquet` |

---

## 2. Selection Rationale & Design Philosophy

### Why IEEE-CIS for Dataset A?
- **IEEE-CIS** is the premier public benchmark for transaction-level fraud detection, containing rich card, device, email, address, and temporal features.
- Provides realistic fraud imbalance (~3.5% fraud rate) and real-world missingness patterns.

### Why Synthetic Scenarios for Dataset B?
- Real merchant-level temporal transaction streams during actual active fraud spikes contain sensitive merchant business metrics and cannot be shared publicly.
- Evaluating defensive detection systems requires explicit **hard negatives** (e.g. flash sales causes high transaction volume without fraud spike, or bulk order price changes causing amount shifts). Synthetic scenario generation allows precise, controllable benchmarking against these hard negative conditions.

### Why LLM Parameter Specs + Local NumPy Row Generation?
- **Cost & Speed**: Prompting an LLM to generate millions of individual numerical CSV rows is prohibitively slow and expensive.
- **Deterministic Reproducibility**: Using NVIDIA Build API (`https://integrate.api.nvidia.com/v1`) strictly to emit abstract statistical scenario parameter JSON (duration, baseline rate, spike multiplier, etc.) allows NumPy to deterministically generate exact numeric transactions via random seeds.
- **Auditability**: Avoids LLM numerical hallucinations and guarantees exact mathematical bounds on velocities, fraud rates, and timestamps.

---

## 3. Dataset Specifications & Feature Groups

### Dataset A — Model Dataset (IEEE-CIS)
- **Schema Columns**: `TransactionID`, `event_time`, `amount`, `amount_log1p`, `ProductCD`, `card1`–`card6`, `addr1`, `addr2`, `P_emaildomain`, `R_emaildomain`, `DeviceType`, `DeviceInfo`, `customer_proxy_id`, `device_proxy_id`, `hour`, `day_of_week`, `is_weekend`, `identity_available`, `isFraud`, `split`.
- **Note on Timestamps**: IEEE-CIS `TransactionDT` is a relative offset in seconds. In Dataset A, it is mapped to a synthetic reference timestamp (`2017-12-01T00:00:00Z` + `TransactionDT`) strictly for temporal ordering. *It does not represent real calendar timestamps.*

### Dataset B — Defensive Synthetic Scenario Dataset
Dataset B simulates merchant transaction streams across 4 scenario types:
1. `normal`: Standard transaction volume and baseline fraud rate ($\text{fraud\_spike} = 0$).
2. `fraud_spike`: Material spike in fraud rate during a temporal window ($\text{fraud\_spike} = 1$).
3. `volume_only_spike` (**Hard Negative**): Flash sale or marketing surge. Transaction volume increases 2.5x–7x, but fraud rate remains at baseline ($\text{fraud\_spike} = 0$).
4. `amount_shift` (**Hard Negative**): Shift in average purchase amounts (e.g. seasonal bulk buys) while fraud rate stays baseline ($\text{fraud\_spike} = 0$).

**Temporal Features Generated for Dataset B**:
- `merchant_txn_count_15m`: Rolling 15-minute transaction count.
- `rolling_fraud_rate_15m`: Rolling 15-minute fraud rate.
- `baseline_txn_15m`: Baseline 15-minute expected transaction volume (computed from early non-spike window).
- `baseline_fraud_rate`: Baseline historical fraud rate.
- `velocity_ratio`: $\text{rolling\_txn\_15m} / \text{baseline\_txn\_15m}$.
- `fraud_rate_deviation`: $\text{rolling\_fraud\_rate\_15m} - \text{baseline\_fraud\_rate}$.
- `baseline_amount` & `amount_deviation`: Amount deviation relative to early baseline.

---

## 4. Temporal Split & Leakage Prevention

- **Dataset A Split**: Strict **chronological split** (70% Train, 15% Validation, 15% Test) based on `event_time`. Ensures $\max(\text{train.event\_time}) \le \min(\text{val.event\_time}) \le \min(\text{test.event\_time})$.
- **Dataset B Split**: **Scenario-level split** (70% Train, 15% Validation, 15% Test). All transaction rows belonging to a specific `scenario_id` are strictly assigned to a single split, preventing scenario data leakage between train and evaluation sets.
- **Baseline Feature Isolation**: Rolling baselines for Dataset B are computed exclusively using historical observations from the initial non-spike baseline window (first 30 minutes) to prevent future temporal leakage.

---

## 5. Environment Variables & Setup

Create a `.env` file or export the following environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `KAGGLE_API_TOKEN` | Token for downloading Kaggle datasets | Required for public data |
| `NVIDIA_API_KEY` | Key for NVIDIA Build API | Required for online scenario specs |
| `NVIDIA_MODEL` | NVIDIA hosted LLM model name | `openai/gpt-oss-20b` |
| `NVIDIA_WORKERS` | Number of parallel worker threads | `4` |
| `SYNTHETIC_SCENARIOS` | Total synthetic scenarios to generate | `60` |

---

## 6. Execution Commands

From the project root:

```bash
# 1. Activate conda environment
conda activate thermo_agent

# 2. Download public IEEE-CIS dataset (requires Kaggle API Token & rules acceptance)
python data.py --download-public

# 3. Build Dataset A (Model Dataset)
python data.py --build-model

# 4. Generate Dataset B via NVIDIA API (Online Mode)
python data.py --generate-scenarios --scenarios 60 --workers 4 --batch-size 5

# 5. Generate Dataset B Offline (Fallback local specification generation)
python data.py --generate-scenarios --scenarios 8 --offline-synthetic

# 6. Run complete end-to-end data pipeline
python data.py --all --scenarios 60 --workers 4 --batch-size 5
```

---

## 7. Dataset Limitations & Disclaimers

- Dataset B is synthetically generated for defensive benchmark evaluation and does not contain real merchant or customer transaction data.
- Dataset A timestamps are synthetic reference values derived from IEEE-CIS relative offsets.
