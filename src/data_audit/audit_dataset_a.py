"""
audit_dataset_a.py
------------------
Audits Dataset A transaction-level model dataset (IEEE-CIS derived).

Performs structural and statistical verification:
  - target distribution
  - missingness per column
  - duplicates
  - chronological ordering
  - train/validation/test time boundaries
  - fraud distribution by split
  - amount distribution by split
  - categorical cardinality
  - constant columns
  - potential target leakage columns

Output:
  - data/processed/dataset_a_audit.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("audit-dataset-a")


def audit_dataset_a(parquet_path: Path | None = None) -> dict[str, Any]:
    if parquet_path is None:
        parquet_path = PROCESSED_DIR / "dataset_a_model.parquet"

    if not parquet_path.exists():
        raise FileNotFoundError(f"Dataset A file not found: {parquet_path}")

    LOGGER.info("Loading Dataset A from %s ...", parquet_path)
    df = pd.read_parquet(parquet_path)

    # 1. Target distribution
    total_rows = len(df)
    fraud_count = int(df["isFraud"].sum())
    non_fraud_count = total_rows - fraud_count
    fraud_pct = round(float(fraud_count / total_rows * 100), 4)

    # 2. Missingness per column
    missing_counts = df.isna().sum().to_dict()
    missing_pcts = (df.isna().mean() * 100).round(4).to_dict()
    missingness = {
        col: {"count": int(missing_counts[col]), "percentage": float(missing_pcts[col])}
        for col in df.columns
    }

    # 3. Duplicates
    dup_tx_ids = int(df["TransactionID"].duplicated().sum())

    # 4. Chronological ordering
    is_ordered = bool(df["event_time"].is_monotonic_increasing)

    # 5. Train/Val/Test boundaries & fraud distribution
    splits = {}
    amount_by_split = {}
    fraud_by_split = {}

    for split_name in ["train", "validation", "test"]:
        sub = df[df["split"] == split_name]
        if not sub.empty:
            s_min = str(sub["event_time"].min())
            s_max = str(sub["event_time"].max())
            s_fraud = int(sub["isFraud"].sum())
            s_total = len(sub)
            s_fraud_pct = round(float(s_fraud / s_total * 100), 4)

            splits[split_name] = {
                "rows": s_total,
                "min_event_time": s_min,
                "max_event_time": s_max,
                "fraud_count": s_fraud,
                "fraud_percentage": s_fraud_pct,
            }

            amt_series = sub["amount"]
            amount_by_split[split_name] = {
                "min": round(float(amt_series.min()), 2),
                "max": round(float(amt_series.max()), 2),
                "mean": round(float(amt_series.mean()), 2),
                "std": round(float(amt_series.std()), 2),
                "median": round(float(amt_series.median()), 2),
            }

    # Verify split boundary ordering
    train_max = df[df["split"] == "train"]["event_time"].max()
    val_min = df[df["split"] == "validation"]["event_time"].min()
    val_max = df[df["split"] == "validation"]["event_time"].max()
    test_min = df[df["split"] == "test"]["event_time"].min()

    boundary_valid = (train_max <= val_min) and (val_max <= test_min)

    # 6. Categorical cardinality
    cat_cols = [
        col for col in [
            "ProductCD", "card1", "card2", "card3", "card4", "card5", "card6",
            "addr1", "addr2", "P_emaildomain", "R_emaildomain", "DeviceType",
            "DeviceInfo", "customer_proxy_id", "device_proxy_id"
        ] if col in df.columns
    ]
    cardinality = {col: int(df[col].nunique(dropna=False)) for col in cat_cols}

    # 7. Constant columns
    constant_columns = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]

    # 8. Potential leakage columns (|corr| > 0.95 with target)
    num_cols = df.select_dtypes(include=[np.number]).columns
    potential_leakage = []
    for col in num_cols:
        if col != "isFraud":
            corr = float(df[col].corr(df["isFraud"]))
            if not np.isnan(corr) and abs(corr) > 0.95:
                potential_leakage.append({"column": col, "correlation": round(corr, 4)})

    audit_json = {
        "dataset": "Dataset A (IEEE-CIS Model Dataset)",
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "target_distribution": {
            "fraud_count": fraud_count,
            "non_fraud_count": non_fraud_count,
            "fraud_percentage": fraud_pct,
        },
        "duplicate_transaction_ids": dup_tx_ids,
        "chronological_ordering_valid": is_ordered,
        "split_boundary_valid": boundary_valid,
        "splits": splits,
        "amount_distribution_by_split": amount_by_split,
        "missingness": missingness,
        "categorical_cardinality": cardinality,
        "constant_columns": constant_columns,
        "potential_leakage_columns": potential_leakage,
    }

    json_path = PROCESSED_DIR / "dataset_a_audit.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(audit_json, f, indent=2)

    LOGGER.info("Dataset A audit JSON written to %s", json_path)
    return audit_json


if __name__ == "__main__":
    audit_dataset_a()
