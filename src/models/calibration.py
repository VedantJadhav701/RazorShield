"""
calibration.py
--------------
Probability calibration for Dataset A transaction model.

Compares:
  1. Raw XGBoost probabilities
  2. Sigmoid calibration (Platt scaling)
  3. Isotonic calibration

Uses Validation set ONLY for fitting calibration.
Evaluates Brier Score, Log Loss, and Expected Calibration Error (ECE).
Selects and freezes the best calibration method for Test evaluation.

Outputs:
  - models/transaction_model/calibrated_model.joblib
  - data/processed/calibration_report.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss, log_loss

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("probability-calibration")

NUMERIC_FEATURES = [
    "amount", "amount_log1p", "hour", "day_of_week", "is_weekend",
    "customer_txn_count_past", "customer_amount_mean_past", "customer_amount_std_past",
    "device_txn_count_past", "customer_amount_dev", "identity_available",
    "missing_p_email", "missing_r_email", "missing_addr1", "missing_device_info"
]

CATEGORICAL_FEATURES = [
    "ProductCD", "card1", "card2", "card3", "card4", "card5", "card6",
    "addr1", "addr2", "P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"
]


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Computes Expected Calibration Error (ECE)."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        bin_size = np.sum(mask)
        if bin_size > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (bin_size / total_samples) * abs(bin_acc - bin_conf)

    return float(ece)


def evaluate_calibration_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Calculates Brier Score, Log Loss, and ECE."""
    brier = float(brier_score_loss(y_true, y_prob))
    loss = float(log_loss(y_true, y_prob))
    ece = compute_ece(y_true, y_prob)
    return {
        "brier_score": round(brier, 6),
        "log_loss": round(loss, 6),
        "ece": round(ece, 6),
    }


def fit_and_evaluate_calibration(
    dataset_a_path: Path | None = None,
) -> dict[str, Any]:
    if dataset_a_path is None:
        dataset_a_path = PROCESSED_DIR / "dataset_a_features.parquet"

    df_a = pd.read_parquet(dataset_a_path)
    val_df = df_a[df_a["split"] == "validation"].copy()
    test_df = df_a[df_a["split"] == "test"].copy()

    tx_model_path = MODELS_DIR / "transaction_model" / "xgboost_model.joblib"
    encoder_path = MODELS_DIR / "transaction_model" / "encoder.joblib"

    if not tx_model_path.exists():
        raise FileNotFoundError(f"Base transaction model not found at {tx_model_path}")

    xgb_tx = joblib.load(tx_model_path)
    encoder = joblib.load(encoder_path)

    val_cat = encoder.transform(val_df[CATEGORICAL_FEATURES].astype(str))
    X_val = np.hstack([val_df[NUMERIC_FEATURES].values.astype(np.float32), val_cat.astype(np.float32)])
    y_val = val_df["isFraud"].values.astype(int)

    test_cat = encoder.transform(test_df[CATEGORICAL_FEATURES].astype(str))
    X_test = np.hstack([test_df[NUMERIC_FEATURES].values.astype(np.float32), test_cat.astype(np.float32)])
    y_test = test_df["isFraud"].values.astype(int)

    # 1. Raw XGBoost probabilities
    val_prob_raw = xgb_tx.predict_proba(X_val)[:, 1]
    test_prob_raw = xgb_tx.predict_proba(X_test)[:, 1]

    raw_val_m = evaluate_calibration_metrics(y_val, val_prob_raw)
    raw_test_m = evaluate_calibration_metrics(y_test, test_prob_raw)

    # 2. Sigmoid Calibration (Platt scaling fitted strictly on Validation probabilities)
    LOGGER.info("Fitting Sigmoid probability calibration on Validation set ...")
    from sklearn.linear_model import LogisticRegression
    from sklearn.isotonic import IsotonicRegression

    cal_sigmoid = LogisticRegression(C=1e5, solver="lbfgs")
    cal_sigmoid.fit(val_prob_raw.reshape(-1, 1), y_val)

    val_prob_sig = cal_sigmoid.predict_proba(val_prob_raw.reshape(-1, 1))[:, 1]
    test_prob_sig = cal_sigmoid.predict_proba(test_prob_raw.reshape(-1, 1))[:, 1]

    sig_val_m = evaluate_calibration_metrics(y_val, val_prob_sig)
    sig_test_m = evaluate_calibration_metrics(y_test, test_prob_sig)

    # 3. Isotonic Calibration (fitted strictly on Validation probabilities)
    LOGGER.info("Fitting Isotonic probability calibration on Validation set ...")
    cal_isotonic = IsotonicRegression(out_of_bounds="clip")
    cal_isotonic.fit(val_prob_raw, y_val)

    val_prob_iso = cal_isotonic.transform(val_prob_raw)
    test_prob_iso = cal_isotonic.transform(test_prob_raw)

    iso_val_m = evaluate_calibration_metrics(y_val, val_prob_iso)
    iso_test_m = evaluate_calibration_metrics(y_test, test_prob_iso)

    methods = {
        "raw": {"val": raw_val_m, "test": raw_test_m, "model": xgb_tx},
        "sigmoid": {"val": sig_val_m, "test": sig_test_m, "model": cal_sigmoid},
        "isotonic": {"val": iso_val_m, "test": iso_test_m, "model": cal_isotonic},
    }

    # Select best calibration method based on Validation Brier Score
    best_method = min(methods.keys(), key=lambda m: methods[m]["val"]["brier_score"])
    LOGGER.info("Selected best calibration method: %s (Val Brier=%.6f, Val LogLoss=%.6f)", 
                best_method, methods[best_method]["val"]["brier_score"], methods[best_method]["val"]["log_loss"])

    # Save calibrated model artifact
    cal_model_path = MODELS_DIR / "transaction_model" / "calibrated_model.joblib"
    joblib.dump(methods[best_method]["model"], cal_model_path)

    report = {
        "dataset": "Dataset A Transaction Model Calibration",
        "selected_calibration_method": best_method,
        "methods": {
            k: {"validation": v["val"], "test": v["test"]}
            for k, v in methods.items()
        },
    }

    json_path = PROCESSED_DIR / "calibration_report.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    LOGGER.info("Calibration report saved to %s", json_path)
    return report


if __name__ == "__main__":
    fit_and_evaluate_calibration()
