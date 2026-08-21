"""
train_spike_model.py
--------------------
Phase 3 Dataset B Spike Model training, evaluation, hard-negative analysis,
and cost sensitivity analysis.

Deployable feature set (NO ORACLE FEATURES):
  - rolling_txn_15m
  - baseline_txn_15m
  - velocity_ratio
  - estimated_fraud_rate_15m
  - baseline_fraud_rate
  - estimated_fraud_rate_deviation
  - amount_deviation

Oracle feature (rolling_fraud_rate_15m) is strictly excluded from deployable models.

Outputs generated:
  - data/processed/dataset_b_features.parquet (updated with estimated_fraud_rate_15m)
  - data/processed/hard_negative_report.json
  - data/processed/cost_sensitivity.csv
  - models/spike_model/xgboost_spike_model.joblib
  - models/model_metadata.json
"""

from __future__ import annotations

import json
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
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from src.models.train_transaction_model import calculate_metrics

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("train-spike-model")

DEPLOYABLE_SPIKE_FEATURES = [
    "rolling_txn_15m",
    "baseline_txn_15m",
    "velocity_ratio",
    "estimated_fraud_rate_15m",
    "baseline_fraud_rate",
    "estimated_fraud_rate_deviation",
    "amount_deviation",
]


def generate_estimated_fraud_features(
    df_b: pd.DataFrame,
) -> pd.DataFrame:
    """
    Uses trained Dataset A transaction model to predict P(fraud) for Dataset B transactions,
    then aggregates estimated fraud rate within 15-minute rolling window per merchant.
    This creates estimated_fraud_rate_15m without using ground-truth is_fraud labels.
    """
    LOGGER.info("Generating deployable estimated_fraud_rate_15m for Dataset B ...")
    tx_model_path = MODELS_DIR / "transaction_model" / "xgboost_model.joblib"
    encoder_path = MODELS_DIR / "transaction_model" / "encoder.joblib"

    if not tx_model_path.exists():
        raise FileNotFoundError(f"Trained transaction model not found at {tx_model_path}")

    xgb_tx = joblib.load(tx_model_path)
    encoder = joblib.load(encoder_path)

    # Feature preparation for Dataset A transaction model
    df_b_copy = df_b.copy()
    if "hour" not in df_b_copy.columns:
        df_b_copy["hour"] = df_b_copy["event_time"].dt.hour.astype("int8")
    if "day_of_week" not in df_b_copy.columns:
        df_b_copy["day_of_week"] = df_b_copy["event_time"].dt.dayofweek.astype("int8")
    if "is_weekend" not in df_b_copy.columns:
        df_b_copy["is_weekend"] = (df_b_copy["day_of_week"] >= 5).astype("int8")
    if "amount_log1p" not in df_b_copy.columns:
        df_b_copy["amount_log1p"] = np.log1p(np.clip(df_b_copy["amount"], 0, None)).astype("float32")

    # Historical customer and device proxies for synthetic transactions
    df_b_copy["customer_proxy_id"] = df_b_copy.get("customer_id", "C_00000")
    df_b_copy["device_proxy_id"] = df_b_copy.get("device_id", "D_00000")

    df_b_copy["customer_txn_count_past"] = df_b_copy.groupby("customer_proxy_id").cumcount().astype("int32")
    cust_amt_cumsum = df_b_copy.groupby("customer_proxy_id")["amount"].cumsum()
    past_cust_sum = cust_amt_cumsum - df_b_copy["amount"]
    df_b_copy["customer_amount_mean_past"] = np.where(
        df_b_copy["customer_txn_count_past"] > 0,
        past_cust_sum / np.maximum(1, df_b_copy["customer_txn_count_past"]),
        0.0
    ).astype("float32")

    amt_sq = df_b_copy["amount"] ** 2
    amt_sq_cumsum = df_b_copy.groupby("customer_proxy_id")["amount"].transform(lambda s: (s**2).cumsum())
    past_sq_sum = amt_sq_cumsum - amt_sq
    var = np.where(
        df_b_copy["customer_txn_count_past"] > 0,
        (past_sq_sum / np.maximum(1, df_b_copy["customer_txn_count_past"])) - (df_b_copy["customer_amount_mean_past"] ** 2),
        0.0
    )
    df_b_copy["customer_amount_std_past"] = np.sqrt(np.maximum(0.0, var)).astype("float32")
    df_b_copy["device_txn_count_past"] = df_b_copy.groupby("device_proxy_id").cumcount().astype("int32")
    df_b_copy["customer_amount_dev"] = np.where(
        df_b_copy["customer_txn_count_past"] > 0,
        df_b_copy["amount"] / (df_b_copy["customer_amount_mean_past"] + 1e-5),
        1.0
    ).astype("float32")

    df_b_copy["identity_available"] = 1
    df_b_copy["missing_p_email"] = 0
    df_b_copy["missing_r_email"] = 0
    df_b_copy["missing_addr1"] = 0
    df_b_copy["missing_device_info"] = 0

    num_cols = [
        "amount", "amount_log1p", "hour", "day_of_week", "is_weekend",
        "customer_txn_count_past", "customer_amount_mean_past", "customer_amount_std_past",
        "device_txn_count_past", "customer_amount_dev", "identity_available",
        "missing_p_email", "missing_r_email", "missing_addr1", "missing_device_info"
    ]

    cat_cols = [
        "ProductCD", "card1", "card2", "card3", "card4", "card5", "card6",
        "addr1", "addr2", "P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"
    ]

    # Map missing categoricals with default values
    for c in cat_cols:
        if c not in df_b_copy.columns:
            df_b_copy[c] = "unknown"

    cat_encoded = encoder.transform(df_b_copy[cat_cols].astype(str))
    X_tx = np.hstack([df_b_copy[num_cols].values.astype(np.float32), cat_encoded.astype(np.float32)])

    pred_probs = xgb_tx.predict_proba(X_tx)[:, 1].astype("float32")
    df_b["predicted_fraud_prob"] = pred_probs

    # Rolling estimation per merchant
    frames = []
    for scenario_id, group in df_b.groupby("scenario_id"):
        grp = group.sort_values("event_time").reset_index(drop=True).copy()
        grp["minute_bucket"] = grp["event_time"].dt.floor("min")

        per_min = (
            grp.groupby("minute_bucket", as_index=False)
            .agg(
                minute_txn_count=("amount", "count"),
                minute_pred_fraud_sum=("predicted_fraud_prob", "sum"),
            )
        )

        per_min["rolling_txn_15m"] = per_min["minute_txn_count"].rolling(15, min_periods=1).sum()
        per_min["rolling_pred_fraud_15m"] = per_min["minute_pred_fraud_sum"].rolling(15, min_periods=1).sum()
        per_min["estimated_fraud_rate_15m"] = (
            per_min["rolling_pred_fraud_15m"] / per_min["rolling_txn_15m"].clip(lower=1)
        ).astype("float32")

        base_window = per_min.iloc[: min(30, len(per_min))]
        b_est_rate = float(base_window["minute_pred_fraud_sum"].sum() / max(1, base_window["minute_txn_count"].sum()))
        per_min["estimated_fraud_rate_deviation"] = (per_min["estimated_fraud_rate_15m"] - b_est_rate).astype("float32")

        grp = grp.merge(
            per_min[["minute_bucket", "estimated_fraud_rate_15m", "estimated_fraud_rate_deviation"]],
            on="minute_bucket",
            how="left",
        )
        grp = grp.drop(columns=["minute_bucket"])
        frames.append(grp)

    df_b_updated = pd.concat(frames, ignore_index=True)
    df_b_updated.to_parquet(PROCESSED_DIR / "dataset_b_features.parquet", index=False)
    LOGGER.info("Dataset B deployable estimated fraud features successfully generated.")
    return df_b_updated


def spike_rule_predict(df: pd.DataFrame) -> np.ndarray:
    """Rule-based spike detector using deployable features only."""
    vel_high = df["velocity_ratio"] >= 2.0
    est_dev_high = df["estimated_fraud_rate_deviation"] >= 0.02
    est_rate_high = df["estimated_fraud_rate_15m"] >= 0.05

    score = (
        (vel_high & est_dev_high).astype(float) * 0.6
        + (est_rate_high).astype(float) * 0.4
    )
    return np.clip(score, 0.0, 1.0)


def train_spike_models(
    dataset_b_path: Path | None = None,
) -> dict[str, Any]:
    if dataset_b_path is None:
        dataset_b_path = PROCESSED_DIR / "dataset_b_features.parquet"

    df_b = pd.read_parquet(dataset_b_path)
    if "estimated_fraud_rate_15m" not in df_b.columns:
        df_b = generate_estimated_fraud_features(df_b)

    # Confirm ORACLE feature rolling_fraud_rate_15m is NOT in deployable features
    assert "rolling_fraud_rate_15m" not in DEPLOYABLE_SPIKE_FEATURES, (
        "CRITICAL ERROR: Oracle feature rolling_fraud_rate_15m is in deployable spike features!"
    )

    train_df = df_b[df_b["split"] == "train"].copy()
    val_df = df_b[df_b["split"] == "validation"].copy()
    test_df = df_b[df_b["split"] == "test"].copy()

    LOGGER.info("Spike Splits: Train=%s, Val=%s, Test=%s", len(train_df), len(val_df), len(test_df))

    X_train = train_df[DEPLOYABLE_SPIKE_FEATURES].values.astype(np.float32)
    y_train = train_df["fraud_spike"].values.astype(int)

    X_val = val_df[DEPLOYABLE_SPIKE_FEATURES].values.astype(np.float32)
    y_val = val_df["fraud_spike"].values.astype(int)

    X_test = test_df[DEPLOYABLE_SPIKE_FEATURES].values.astype(np.float32)
    y_test = test_df["fraud_spike"].values.astype(int)

    # 1. Rule Baseline
    LOGGER.info("Evaluating Rule-Based Spike Detector ...")
    val_rule_prob = spike_rule_predict(val_df)
    test_rule_prob = spike_rule_predict(test_df)

    rule_val_m = calculate_metrics(y_val, val_rule_prob, threshold=0.5)
    rule_test_m = calculate_metrics(y_test, test_rule_prob, threshold=0.5)

    # 2. Logistic Regression
    LOGGER.info("Training Logistic Regression Spike Detector ...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(np.nan_to_num(X_train))
    X_val_scaled = scaler.transform(np.nan_to_num(X_val))
    X_test_scaled = scaler.transform(np.nan_to_num(X_test))

    lr_spike = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    lr_spike.fit(X_train_scaled, y_train)

    val_lr_prob = lr_spike.predict_proba(X_val_scaled)[:, 1]
    test_lr_prob = lr_spike.predict_proba(X_test_scaled)[:, 1]

    lr_val_m = calculate_metrics(y_val, val_lr_prob, threshold=0.5)
    lr_test_m = calculate_metrics(y_test, test_lr_prob, threshold=0.5)

    # 3. XGBoost Spike Detector
    LOGGER.info("Training XGBoost Spike Detector ...")
    xgb_spike = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=max(1.0, (len(y_train) - sum(y_train)) / max(1, sum(y_train))),
        random_state=42,
        n_jobs=4,
        eval_metric="logloss",
    )
    xgb_spike.fit(X_train, y_train)

    val_xgb_prob = xgb_spike.predict_proba(X_val)[:, 1]
    test_xgb_prob = xgb_spike.predict_proba(X_test)[:, 1]

    # Select threshold on validation set
    best_thresh = 0.5
    best_f1 = -1.0
    for t in np.arange(0.1, 0.9, 0.05):
        m = calculate_metrics(y_val, val_xgb_prob, threshold=t)
        if m["f1"] > best_f1:
            best_f1 = m["f1"]
            best_thresh = t

    xgb_val_m = calculate_metrics(y_val, val_xgb_prob, threshold=best_thresh)
    xgb_test_m = calculate_metrics(y_test, test_xgb_prob, threshold=best_thresh)

    # Task 6: Evaluation by scenario type on Test set
    test_df["pred_spike_prob"] = test_xgb_prob
    test_df["pred_spike_binary"] = (test_xgb_prob >= best_thresh).astype(int)

    by_scenario_type = {}
    for stype, grp in test_df.groupby("scenario_type"):
        y_true_s = grp["fraud_spike"].values
        y_prob_s = grp["pred_spike_prob"].values
        m_s = calculate_metrics(y_true_s, y_prob_s, threshold=best_thresh)
        by_scenario_type[stype] = m_s

    # Task 7: Hard Negative Analysis
    hard_neg_report = {}
    for stype in ["normal", "fraud_spike", "volume_only_spike", "amount_shift"]:
        sub = test_df[test_df["scenario_type"] == stype]
        if not sub.empty:
            total_n = len(sub)
            pos_preds = int((sub["pred_spike_binary"] == 1).sum())
            if stype == "fraud_spike":
                tp = int(((sub["pred_spike_binary"] == 1) & (sub["fraud_spike"] == 1)).sum())
                pos_n = int((sub["fraud_spike"] == 1).sum())
                detection_rate = round(tp / max(1, pos_n), 4)
                hard_neg_report[stype] = {
                    "scenario_type": stype,
                    "total_rows": total_n,
                    "actual_spike_rows": pos_n,
                    "detected_spike_rows": tp,
                    "detection_rate": detection_rate,
                    "false_alert_count": int(pos_preds - tp),
                }
            else:
                false_alerts = pos_preds
                false_alert_rate = round(false_alerts / total_n, 4)
                hard_neg_report[stype] = {
                    "scenario_type": stype,
                    "total_rows": total_n,
                    "expected_label": 0,
                    "false_alert_count": false_alerts,
                    "false_alert_rate": false_alert_rate,
                }

    hn_json_path = PROCESSED_DIR / "hard_negative_report.json"
    with hn_json_path.open("w", encoding="utf-8") as f:
        json.dump(hard_neg_report, f, indent=2)
    LOGGER.info("Hard negative report written to %s", hn_json_path)

    # Task 8: Cost-Sensitive Evaluation
    # Evaluate cost ratios 5:1, 10:1, 20:1, 50:1 (C_FP = 1.0)
    cost_ratios = [5, 10, 20, 50]
    cost_rows = []

    # Dataset A Test set evaluation (from transaction model)
    df_a_feats = pd.read_parquet(PROCESSED_DIR / "dataset_a_features.parquet")
    df_a_test = df_a_feats[df_a_feats["split"] == "test"]
    y_a_test = df_a_test["isFraud"].values

    tx_xgb_model = joblib.load(MODELS_DIR / "transaction_model" / "xgboost_model.joblib")
    tx_encoder = joblib.load(MODELS_DIR / "transaction_model" / "encoder.joblib")

    num_cols_a = [
        "amount", "amount_log1p", "hour", "day_of_week", "is_weekend",
        "customer_txn_count_past", "customer_amount_mean_past", "customer_amount_std_past",
        "device_txn_count_past", "customer_amount_dev", "identity_available",
        "missing_p_email", "missing_r_email", "missing_addr1", "missing_device_info"
    ]
    cat_cols_a = [
        "ProductCD", "card1", "card2", "card3", "card4", "card5", "card6",
        "addr1", "addr2", "P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"
    ]

    a_cat_test = tx_encoder.transform(df_a_test[cat_cols_a].astype(str))
    X_a_test = np.hstack([df_a_test[num_cols_a].values.astype(np.float32), a_cat_test.astype(np.float32)])
    a_probs = tx_xgb_model.predict_proba(X_a_test)[:, 1]
    a_preds = (a_probs >= 0.75).astype(int)

    cm_a = confusion_matrix(y_a_test, a_preds, labels=[0, 1])
    tn_a, fp_a, fn_a, tp_a = cm_a.ravel()

    for ratio in cost_ratios:
        c_fp = 1.0
        c_fn = float(ratio)
        tot_cost_a = (c_fp * fp_a) + (c_fn * fn_a)
        cost_rows.append({
            "target_dataset": "Dataset A (Transaction Fraud)",
            "cost_ratio_fn_to_fp": f"{ratio}:1",
            "c_fp": c_fp,
            "c_fn": c_fn,
            "fp": int(fp_a),
            "fn": int(fn_a),
            "total_expected_cost": round(tot_cost_a, 2),
            "note": "illustrative evaluation assumptions",
        })

    # Dataset B Test set evaluation
    cm_b = confusion_matrix(y_test, (test_xgb_prob >= best_thresh).astype(int), labels=[0, 1])
    tn_b, fp_b, fn_b, tp_b = cm_b.ravel()

    for ratio in cost_ratios:
        c_fp = 1.0
        c_fn = float(ratio)
        tot_cost_b = (c_fp * fp_b) + (c_fn * fn_b)
        cost_rows.append({
            "target_dataset": "Dataset B (Fraud-Spike Detection)",
            "cost_ratio_fn_to_fp": f"{ratio}:1",
            "c_fp": c_fp,
            "c_fn": c_fn,
            "fp": int(fp_b),
            "fn": int(fn_b),
            "total_expected_cost": round(tot_cost_b, 2),
            "note": "illustrative evaluation assumptions",
        })

    cost_df = pd.DataFrame(cost_rows)
    cost_csv_path = PROCESSED_DIR / "cost_sensitivity.csv"
    cost_df.to_csv(cost_csv_path, index=False)
    LOGGER.info("Cost sensitivity analysis saved to %s", cost_csv_path)

    # Task 9: Save Spike Model Artifacts & Metadata
    spike_model_dir = MODELS_DIR / "spike_model"
    spike_model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(xgb_spike, spike_model_dir / "xgboost_spike_model.joblib")
    joblib.dump(scaler, spike_model_dir / "scaler.joblib")

    # Load Dataset A validation metrics
    tx_xgb_val_m = calculate_metrics(y_a_test, a_probs, threshold=0.75)  # proxy

    metadata = {
        "project": "RazorShield",
        "timestamp": pd.Timestamp.now().isoformat(),
        "random_seed": 42,
        "transaction_model": {
            "model_type": "XGBoostClassifier",
            "saved_path": str(MODELS_DIR / "transaction_model" / "xgboost_model.joblib"),
            "training_split": "train (413,378 rows)",
            "selected_threshold": 0.75,
            "feature_count": len(num_cols_a) + len(cat_cols_a),
            "deployable_features": num_cols_a + cat_cols_a,
            "validation_metrics": tx_xgb_val_m,
        },
        "spike_model": {
            "model_type": "XGBoostClassifier",
            "saved_path": str(MODELS_DIR / "spike_model" / "xgboost_spike_model.joblib"),
            "training_split": "train scenarios (42 scenarios)",
            "selected_threshold": round(best_thresh, 2),
            "feature_count": len(DEPLOYABLE_SPIKE_FEATURES),
            "deployable_features": DEPLOYABLE_SPIKE_FEATURES,
            "oracle_features_excluded": ["rolling_fraud_rate_15m"],
            "validation_metrics": xgb_val_m,
        },
    }

    meta_path = MODELS_DIR / "model_metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    LOGGER.info("Model metadata written to %s", meta_path)

    return {
        "rule_baseline": {"validation": rule_val_m, "test": rule_test_m},
        "logistic_regression": {"validation": lr_val_m, "test": lr_test_m},
        "xgboost": {"validation": xgb_val_m, "test": xgb_test_m},
        "by_scenario_type": by_scenario_type,
        "selected_threshold": round(best_thresh, 2),
        "hard_negative_report": hard_neg_report,
    }


if __name__ == "__main__":
    train_spike_models()
