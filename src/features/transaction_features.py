"""
transaction_features.py
------------------------
Leakage-safe transaction-level feature engineering for Dataset A.

Features generated:
  - amount_log1p
  - hour, day_of_week, is_weekend
  - customer_txn_count_past (historical customer transaction count)
  - customer_amount_mean_past (historical customer average amount)
  - customer_amount_std_past (historical customer amount standard deviation)
  - device_txn_count_past (historical device transaction count)
  - customer_amount_dev (amount ratio relative to customer's historical average)
  - missingness indicators (identity_available, missing_p_email, missing_r_email, missing_addr1, missing_device_info)

Guarantees:
  - All rolling/expanding features use strictly observations prior to current transaction index.
  - Zero future data leakage.
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
LOGGER = logging.getLogger("transaction-features")


def generate_dataset_a_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes leakage-free transaction features for Dataset A.
    Assumes df is sorted or will sort df chronologically by event_time.
    """
    LOGGER.info("Generating Dataset A features for %s rows ...", len(df))
    df_out = df.sort_values("event_time").reset_index(drop=True)

    # 1. Basic time features
    df_out["hour"] = df_out["event_time"].dt.hour.astype("int8")
    df_out["day_of_week"] = df_out["event_time"].dt.dayofweek.astype("int8")
    df_out["is_weekend"] = (df_out["day_of_week"] >= 5).astype("int8")

    # 2. Amount log1p
    df_out["amount_log1p"] = np.log1p(np.clip(df_out["amount"], 0, None)).astype("float32")

    # 3. Leakage-safe customer historical features
    cust_group = df_out.groupby("customer_proxy_id")

    # Expanding count of prior transactions
    past_cust_count = cust_group.cumcount().astype("int32")
    df_out["customer_txn_count_past"] = past_cust_count

    # Past sum of amount (cumsum minus current row)
    amt = df_out["amount"].astype("float64")
    amt_cumsum = cust_group["amount"].cumsum()
    past_amt_sum = (amt_cumsum - amt).values

    past_count_arr = past_cust_count.values
    valid_mask = past_count_arr > 0

    past_amt_mean = np.zeros(len(df_out), dtype="float32")
    past_amt_mean[valid_mask] = (past_amt_sum[valid_mask] / past_count_arr[valid_mask]).astype("float32")
    df_out["customer_amount_mean_past"] = past_amt_mean

    # Past variance of amount
    amt_sq = amt ** 2
    amt_sq_cumsum = df_out.groupby("customer_proxy_id")["amount"].transform(lambda s: (s.astype("float64")**2).cumsum())
    past_amt_sq_sum = (amt_sq_cumsum - amt_sq).values

    past_amt_var = np.zeros(len(df_out), dtype="float32")
    past_amt_var[valid_mask] = (
        (past_amt_sq_sum[valid_mask] / past_count_arr[valid_mask]) - (past_amt_mean[valid_mask] ** 2)
    )
    df_out["customer_amount_std_past"] = np.sqrt(np.maximum(0.0, past_amt_var)).astype("float32")

    # Amount deviation from customer past mean
    amt_dev = np.ones(len(df_out), dtype="float32")
    amt_dev[valid_mask] = (
        df_out["amount"].values[valid_mask] / (past_amt_mean[valid_mask] + 1e-5)
    ).astype("float32")
    df_out["customer_amount_dev"] = amt_dev

    # 4. Leakage-safe device historical count
    dev_group = df_out.groupby("device_proxy_id")
    df_out["device_txn_count_past"] = dev_group.cumcount().astype("int32")

    # 5. Missingness indicators
    df_out["identity_available"] = (
        df_out["DeviceInfo"].notna() | df_out["DeviceType"].notna()
    ).astype("int8")
    df_out["missing_p_email"] = df_out["P_emaildomain"].isna().astype("int8")
    df_out["missing_r_email"] = df_out["R_emaildomain"].isna().astype("int8")
    df_out["missing_addr1"] = df_out["addr1"].isna().astype("int8")
    df_out["missing_device_info"] = df_out["DeviceInfo"].isna().astype("int8")

    LOGGER.info("Dataset A feature engineering complete. Total columns: %s", len(df_out.columns))
    return df_out


def build_and_save_dataset_a_features(
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    root = Path(__file__).resolve().parents[2]
    if input_path is None:
        input_path = root / "data" / "processed" / "dataset_a_model.parquet"
    if output_path is None:
        output_path = root / "data" / "processed" / "dataset_a_features.parquet"

    df = pd.read_parquet(input_path)
    df_feats = generate_dataset_a_features(df)
    df_feats.to_parquet(output_path, index=False)
    LOGGER.info("Dataset A features saved to %s", output_path)
    return output_path


if __name__ == "__main__":
    build_and_save_dataset_a_features()
