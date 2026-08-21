# RazorShield — Modeling, Calibration & False-Positive Reduction Documentation

This document describes the modeling methodology, probability calibration, deployable feature isolation, threshold tuning, hard-negative failure investigation, and cost-sensitivity benchmarks for the **RazorShield** defensive AI fraud-spike detection system.

> [!IMPORTANT]
> **Disclaimer**: This document represents offline model training and evaluation benchmarking (Phases 3 & 4). It does **NOT** constitute or claim full production readiness. Further risk engine integration, latency profiling, and real-time streaming validation are required in subsequent phases.

---

## 1. Probability Calibration (Dataset A Transaction Model)

### Why Raw Probability Calibration Was Needed
Raw XGBoost probabilities trained on imbalanced datasets using `scale_pos_weight = 27.5` suffer from severe probability distortion. Raw output scores are shifted upwards, resulting in a high Brier Score (`0.0989`) and an Expected Calibration Error (ECE) of **`21.85%`**. Calibration maps model confidence scores to true empirical probabilities $P(\text{fraud} \mid \text{txn})$.

### Calibration Methods Evaluated (Fitted Strictly on Validation Data)
1. **Raw XGBoost**: Uncalibrated predictions.
2. **Sigmoid Calibration (Platt Scaling)**: Logistic regression fitted on validation prediction logits.
3. **Isotonic Calibration**: Non-parametric isotonic regression fitted on validation prediction probabilities.

### Calibration Benchmarks

| Method | Validation Brier Score | Validation Log Loss | Validation ECE | Test Brier Score | Test Log Loss | Test ECE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw XGBoost** | 0.098948 | 0.342828 | 21.851% | 0.104293 | 0.356667 | 22.567% |
| **Sigmoid (Platt)** | 0.029633 | 0.121364 | 0.210% | 0.030664 | 0.126617 | 0.353% |
| **Isotonic (Selected)** | **0.029433** | **0.120360** | **0.000%** | **0.030629** | **0.126998** | **0.188%** |

*Selection*: **Isotonic Calibration** achieved the minimum Validation Brier score (`0.029433`) and reduced Expected Calibration Error from **21.85% to 0.188%** on the Test set.

---

## 2. Dataset B — Hard Negative Investigation & Feature Improvements

### Volume-Only Hard Negative Failure Analysis
In Phase 3, the deployable spike detector exhibited a **`39.35%` false-alert rate** on `volume_only_spike` scenarios (e.g. flash sales, promotional campaigns).

#### Root Cause
Flash sales generate high transaction volume ($\approx 4.6\text{x}$ baseline). In Phase 3, the model relied heavily on `velocity_ratio` ($\text{rolling\_txn\_15m} / \text{baseline\_txn\_15m}$). Because raw transaction volume surged, the detector triggered false fraud-spike alerts even though the underlying transaction fraud rate remained at baseline (~0.8%).

#### New Deployable Fraud-Excess Features (Phase 4)
To decouple legitimate volume surges from genuine fraud surges, 7 new deployable features were engineered:

1. `fraud_signal_ratio`: $\text{estimated\_fraud\_rate\_15m} / \text{baseline\_fraud\_rate}$
2. `estimated_fraud_count_15m`: Sum of transaction calibrated fraud probabilities $\sum \hat{p}_i$ in the 15-minute window.
3. `expected_fraud_count_15m`: $\text{baseline\_fraud\_rate} \times \text{rolling\_txn\_15m}$
4. `fraud_excess_ratio`: $\text{estimated\_fraud\_count\_15m} / \text{expected\_fraud\_count\_15m}$
5. `volume_deviation`: $\text{rolling\_txn\_15m} / \text{baseline\_txn\_15m}$
6. `fraud_excess_minus_velocity`: $\text{fraud\_excess\_ratio} - \text{velocity\_ratio}$
7. `amount_shift_indicator`: $\text{amount} / \text{baseline\_amount}$

#### Why Fraud-Excess Disambiguates Flash Sales
- **Flash Sales (`volume_only_spike`)**: Both actual volume and expected fraud count increase proportionally. Thus, $\text{fraud\_excess\_ratio} \approx 1.0$ and $\text{fraud\_excess\_minus\_velocity} < 0$, preventing false alerts.
- **Genuine Fraud Spikes (`fraud_spike`)**: Calibrated transaction fraud probabilities surge. Thus, $\text{fraud\_excess\_ratio} \gg 1.0$ ($\approx 16.6\text{x}$) and $\text{fraud\_excess\_minus\_velocity} \gg 0$, triggering valid alerts.

---

## 3. Cost-Sensitive Threshold Optimization Methodology

Threshold optimization is performed strictly on the **Validation set** by minimizing expected financial loss across illustrative cost ratios $C_{\text{FN}} : C_{\text{FP}}$ (where $C_{\text{FP}} = 1.0$):

$$\text{Expected Cost} = (C_{\text{FP}} \times \text{FP}) + (C_{\text{FN}} \times \text{FN})$$

Selected thresholds are frozen and evaluated once on the Test set.

### Cost-Optimized Threshold Results (Dataset B Spike Detector)

| Cost Ratio ($C_{\text{FN}} : C_{\text{FP}}$) | Selected Val Threshold | Val FP | Val FN | Val Expected Cost | Test FP | Test FN | Test Precision | Test Recall | Test Expected Cost |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **5 : 1** | `0.04` | 5,433 | 181 | \$6,338.00 | 3,194 | 150 | 0.4104 | 0.9368 | \$3,944.00 |
| **10 : 1** | `0.04` | 5,433 | 181 | \$7,243.00 | 3,194 | 150 | 0.4104 | 0.9368 | \$4,694.00 |
| **20 : 1** | `0.02` | 6,679 | 91 | \$8,499.00 | 3,981 | 0 | 0.3735 | 1.0000 | \$3,981.00 |
| **50 : 1** | `0.02` | 6,679 | 91 | \$11,229.00 | 3,981 | 0 | 0.3735 | 1.0000 | \$3,981.00 |

---

## 4. Phase 3 vs Phase 4 Comparison Table

| Metric / Scenario | Phase 3 (Baseline) | Phase 4 (Calibrated + Fraud-Excess Features) | Improvement / Difference |
| :--- | :---: | :---: | :---: |
| **Transaction Model ECE** | 21.85% | **0.188%** | **-21.66% ECE (Calibrated)** |
| **Transaction Model Brier Score** | 0.0989 | **0.0294** | **-0.0695 Brier Score** |
| **`volume_only_spike` False Alert Rate** (at $T=0.30$) | 39.35% | **5.27%** | **-34.08% False Alert Reduction** |
| **`amount_shift` False Alert Rate** | 1.21% | **0.00%** | **-1.21% False Alert Reduction** |
| **`normal` False Alert Rate** | 0.39% | **0.00%** | **-0.39% False Alert Reduction** |
| **Fraud Spike Precision** (at $T=0.30$) | 48.51% | **68.24%** | **+19.73% Precision** |
| **Spike Detector ROC-AUC** | 0.8672 | **0.9396** | **+0.0724 ROC-AUC** |

---

## 5. Remaining Limitations

1. **Trade-off between False Alerts & Early Detection**: Tuning the threshold to $T=0.30$ reduces `volume_only_spike` false alerts to 5.27%, but catches fraud spikes during active high-confidence windows.
2. **Merchant Campaign Registration**: Automated detection benefits significantly if merchants register scheduled flash sale windows in advance via API to suppress velocity-triggered warnings.
