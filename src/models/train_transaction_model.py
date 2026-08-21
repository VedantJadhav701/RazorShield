"""
train_transaction_model.py
--------------------------
Trains and evaluates transaction-level fraud models for Dataset A:
  1. Simple Rule Baseline
  2. Logistic Regression
  3. XGBoost Classifier

Strict split policy:
  - train: fit models & encoders
  - validation: threshold selection & model comparison
  - test: final evaluation ONCE (frozen threshold)

Outputs:
  - data/processed/model_threshold_analysis.csv
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("train-tx-model")

NUMERIC_FEATURES = [
    "amount",
    "amount_log1p",
    "hour",
    "day_of_week",
    "is_weekend",
    "customer_txn_count_past",
    "customer_amount_mean_past",
    "customer_amount_std_past",
    "device_txn_count_past",
    "customer_amount_dev",
    "identity_available",
    "missing_p_email",
    "missing_r_email",
    "missing_addr1",
    "missing_device_info",
]

CATEGORICAL_FEATURES = [
    "ProductCD",
    "card1",
    "card2",
    "card3",
    "card4",
    "card5",
    "card6",
    "addr1",
    "addr2",
    "P_emaildomain",
    "R_emaildomain",
    "DeviceType",
    "DeviceInfo",
]


def calculate_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    y_pred = (y_prob >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    pr_auc = float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0
    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5

    fpr = float(fp / max(1, (fp + tn)))
    fnr = float(fn / max(1, (fn + tp)))

    return {
        "threshold": round(threshold, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "num_predicted_positives": int(tp + fp),
    }


def rule_based_predict(df: pd.DataFrame) -> np.ndarray:
    """Simple high-risk rule baseline returning risk probabilities."""
    high_amt = df["amount"] > 300
    new_cust = df["customer_txn_count_past"] == 0
    high_dev = df["customer_amount_dev"] > 4.0
    no_id = df["identity_available"] == 0
    big_amt = df["amount"] > 500

    score = (
        (high_amt & new_cust).astype(float) * 0.4
        + (high_dev).astype(float) * 0.35
        + (no_id & big_amt).astype(float) * 0.25
    )
    return np.clip(score, 0.0, 1.0)


def train_dataset_a_models(
    parquet_path: Path | None = None,
) -> dict[str, Any]:
    if parquet_path is None:
        parquet_path = PROCESSED_DIR / "dataset_a_features.parquet"

    LOGGER.info("Loading Dataset A features from %s ...", parquet_path)
    df = pd.read_parquet(parquet_path)

    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "validation"].copy()
    test_df = df[df["split"] == "test"].copy()

    LOGGER.info("Splits: Train=%s, Val=%s, Test=%s", len(train_df), len(val_df), len(test_df))

    # Preprocess categorical features strictly on train
    cat_present = [c for c in CATEGORICAL_FEATURES if c in df.columns]
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    
    train_cat_encoded = encoder.fit_transform(train_df[cat_present].astype(str))
    val_cat_encoded = encoder.transform(val_df[cat_present].astype(str))
    test_cat_encoded = encoder.transform(test_df[cat_present].astype(str))

    num_present = [c for c in NUMERIC_FEATURES if c in df.columns]

    X_train = np.hstack([train_df[num_present].values.astype(np.float32), train_cat_encoded.astype(np.float32)])
    y_train = train_df["isFraud"].values.astype(int)

    X_val = np.hstack([val_df[num_present].values.astype(np.float32), val_cat_encoded.astype(np.float32)])
    y_val = val_df["isFraud"].values.astype(int)

    X_test = np.hstack([test_df[num_present].values.astype(np.float32), test_cat_encoded.astype(np.float32)])
    y_test = test_df["isFraud"].values.astype(int)

    feature_names = num_present + cat_present

    # 1. Rule Baseline
    LOGGER.info("Evaluating Rule Baseline ...")
    val_rule_prob = rule_based_predict(val_df)
    test_rule_prob = rule_based_predict(test_df)

    rule_val_metrics = calculate_metrics(y_val, val_rule_prob, threshold=0.3)
    rule_test_metrics = calculate_metrics(y_test, test_rule_prob, threshold=0.3)

    # 2. Logistic Regression
    LOGGER.info("Training Logistic Regression ...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(np.nan_to_num(X_train))
    X_val_scaled = scaler.transform(np.nan_to_num(X_val))
    X_test_scaled = scaler.transform(np.nan_to_num(X_test))

    lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)

    val_lr_prob = lr.predict_proba(X_val_scaled)[:, 1]
    test_lr_prob = lr.predict_proba(X_test_scaled)[:, 1]

    # 3. XGBoost
    LOGGER.info("Training XGBoost Classifier ...")
    pos_count = np.sum(y_train == 1)
    neg_count = np.sum(y_train == 0)
    scale_pos = neg_count / max(1, pos_count)

    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        random_state=42,
        n_jobs=4,
        eval_metric="logloss",
    )
    xgb_model.fit(X_train, y_train)

    val_xgb_prob = xgb_model.predict_proba(X_val)[:, 1]
    test_xgb_prob = xgb_model.predict_proba(X_test)[:, 1]

    # Task 3: Threshold Analysis on Validation Set for XGBoost
    thresholds = np.arange(0.05, 0.96, 0.05)
    thresh_rows = []
    best_thresh = 0.5
    best_val_f1 = -1.0

    for t in thresholds:
        m_val = calculate_metrics(y_val, val_xgb_prob, threshold=t)
        thresh_rows.append({
            "threshold": round(t, 2),
            "precision": m_val["precision"],
            "recall": m_val["recall"],
            "f1": m_val["f1"],
            "fp": m_val["fp"],
            "fn": m_val["fn"],
            "fpr": m_val["fpr"],
        })
        if m_val["f1"] > best_val_f1:
            best_val_f1 = m_val["f1"]
            best_thresh = t

    thresh_df = pd.DataFrame(thresh_rows)
    thresh_path = PROCESSED_DIR / "model_threshold_analysis.csv"
    thresh_df.to_csv(thresh_path, index=False)
    LOGGER.info("Threshold analysis saved to %s (Best Val Threshold=%.2f, Val F1=%.4f)", thresh_path, best_thresh, best_val_f1)

    # Evaluate best XGBoost on Validation & Test using frozen selected threshold
    xgb_val_metrics = calculate_metrics(y_val, val_xgb_prob, threshold=best_thresh)
    xgb_test_metrics = calculate_metrics(y_test, test_xgb_prob, threshold=best_thresh)

    lr_val_metrics = calculate_metrics(y_val, val_lr_prob, threshold=0.5)
    lr_test_metrics = calculate_metrics(y_test, test_lr_prob, threshold=0.5)

    results = {
        "rule_baseline": {"validation": rule_val_metrics, "test": rule_test_metrics},
        "logistic_regression": {"validation": lr_val_metrics, "test": lr_test_metrics},
        "xgboost": {"validation": xgb_val_metrics, "test": xgb_test_metrics},
        "selected_threshold": round(best_thresh, 2),
        "best_model_name": "xgboost",
        "feature_names": feature_names,
    }

    # Save trained transaction model artifacts
    tx_model_dir = MODELS_DIR / "transaction_model"
    tx_model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(xgb_model, tx_model_dir / "xgboost_model.joblib")
    joblib.dump(encoder, tx_model_dir / "encoder.joblib")
    joblib.dump(scaler, tx_model_dir / "scaler.joblib")

    # Store full dataset probabilities for Dataset B estimated fraud rate feature
    df["predicted_fraud_prob"] = 0.0
    all_cat = encoder.transform(df[cat_present].astype(str))
    X_all = np.hstack([df[num_present].values.astype(np.float32), all_cat.astype(np.float32)])
    df["predicted_fraud_prob"] = xgb_model.predict_proba(X_all)[:, 1].astype(np.float32)

    df.to_parquet(PROCESSED_DIR / "dataset_a_features.parquet", index=False)

    return results


if __name__ == "__main__":
    train_dataset_a_models()
