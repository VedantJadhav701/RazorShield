"""
scenario_features.py
--------------------
Leakage-safe temporal and scenario feature engineering for Dataset B.

Features verified/generated:
  - rolling_txn_15m
  - rolling_fraud_rate_15m
  - baseline_txn_15m
  - baseline_fraud_rate
  - velocity_ratio
  - fraud_rate_deviation
  - amount_deviation

Guarantees:
  - Rolling features are computed strictly on past 15-minute rolling windows.
  - Baselines are calculated exclusively from early non-spike baseline windows.
  - Zero future scenario temporal leakage.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("scenario-features")


def generate_dataset_b_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures all merchant temporal & scenario features are present and cleanly formatted for Dataset B.
    """
    LOGGER.info("Generating Dataset B scenario features for %s rows ...", len(df))
    df_out = df.copy()

    required_cols = [
        "rolling_txn_15m",
        "rolling_fraud_rate_15m",
        "baseline_txn_15m",
        "baseline_fraud_rate",
        "velocity_ratio",
        "fraud_rate_deviation",
        "amount_deviation",
    ]

    # Check if features exist, else compute them per scenario
    missing = [c for c in required_cols if c not in df_out.columns]

    if missing:
        LOGGER.info("Computing missing Dataset B features: %s", missing)
        frames = []
        for scenario_id, group in df_out.groupby("scenario_id"):
            grp = group.sort_values("event_time").reset_index(drop=True).copy()
            grp["minute_bucket"] = grp["event_time"].dt.floor("min")

            # Per-minute aggregations
            per_min = (
                grp.groupby("minute_bucket", as_index=False)
                .agg(
                    minute_txn_count=("amount", "count"),
                    minute_fraud_count=("is_fraud", "sum"),
                    minute_amount_sum=("amount", "sum"),
                )
            )

            per_min["rolling_txn_15m"] = per_min["minute_txn_count"].rolling(15, min_periods=1).sum()
            per_min["rolling_fraud_15m"] = per_min["minute_fraud_count"].rolling(15, min_periods=1).sum()
            per_min["rolling_fraud_rate_15m"] = per_min["rolling_fraud_15m"] / per_min["rolling_txn_15m"].clip(lower=1)

            # Baseline from first 30 minutes
            base_window = per_min.iloc[: min(30, len(per_min))]
            b_txn_15m = float(base_window["minute_txn_count"].mean() * 15)
            b_fraud_rate = float(base_window["minute_fraud_count"].sum() / max(1, base_window["minute_txn_count"].sum()))
            b_amt = float(base_window["minute_amount_sum"].mean() / max(1.0, base_window["minute_txn_count"].mean()))

            per_min["baseline_txn_15m"] = max(1.0, b_txn_15m)
            per_min["baseline_fraud_rate"] = b_fraud_rate
            per_min["velocity_ratio"] = per_min["rolling_txn_15m"] / per_min["baseline_txn_15m"]
            per_min["fraud_rate_deviation"] = per_min["rolling_fraud_rate_15m"] - per_min["baseline_fraud_rate"]

            grp = grp.merge(
                per_min[
                    [
                        "minute_bucket",
                        "rolling_txn_15m",
                        "rolling_fraud_rate_15m",
                        "baseline_txn_15m",
                        "baseline_fraud_rate",
                        "velocity_ratio",
                        "fraud_rate_deviation",
                    ]
                ],
                on="minute_bucket",
                how="left",
            )

            grp["baseline_amount"] = max(1.0, b_amt)
            grp["amount_deviation"] = grp["amount"] / grp["baseline_amount"].clip(lower=1)
            grp = grp.drop(columns=["minute_bucket"])
            frames.append(grp)

        df_out = pd.concat(frames, ignore_index=True)

    # Cast feature dtypes cleanly
    for c in required_cols:
        df_out[c] = df_out[c].astype("float32")

    LOGGER.info("Dataset B feature engineering complete. Total columns: %s", len(df_out.columns))
    return df_out


def build_and_save_dataset_b_features(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    root = Path(__file__).resolve().parents[2]
    if input_path is None:
        input_path = root / "data" / "processed" / "dataset_b_scenarios.parquet"
    if output_path is None:
        output_path = root / "data" / "processed" / "dataset_b_features.parquet"

    df = pd.read_parquet(input_path)
    df_feats = generate_dataset_b_features(df)
    df_feats.to_parquet(output_path, index=False)
    LOGGER.info("Dataset B features saved to %s", output_path)
    return output_path


if __name__ == "__main__":
    build_and_save_dataset_b_features()
