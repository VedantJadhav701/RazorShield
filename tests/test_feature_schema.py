"""
test_feature_schema.py
----------------------
Unit tests verifying feature schema, dtypes, non-null guarantees, and absence of infinite values.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def dataset_a_features():
    path = DATA_DIR / "dataset_a_features.parquet"
    if not path.exists():
        pytest.skip(f"Feature file not found: {path}")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def dataset_b_features():
    path = DATA_DIR / "dataset_b_features.parquet"
    if not path.exists():
        pytest.skip(f"Feature file not found: {path}")
    return pd.read_parquet(path)


def test_dataset_a_feature_schema(dataset_a_features):
    """Verify Dataset A required engineered features exist and have valid dtypes."""
    expected_cols = [
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

    for col in expected_cols:
        assert col in dataset_a_features.columns, f"Missing required feature column: {col}"


def test_dataset_a_no_infinite_values(dataset_a_features):
    """Verify Dataset A engineered features contain zero infinite values."""
    num_cols = dataset_a_features.select_dtypes(include=[np.number]).columns
    inf_count = np.isinf(dataset_a_features[num_cols]).sum().sum()
    assert inf_count == 0, f"Found {inf_count} infinite values in Dataset A features!"


def test_dataset_a_features_no_nans(dataset_a_features):
    """Verify engineered numerical features in Dataset A have zero NaNs."""
    a_engineered = [
        "amount_log1p",
        "hour",
        "day_of_week",
        "is_weekend",
        "customer_txn_count_past",
        "customer_amount_mean_past",
        "customer_amount_std_past",
        "device_txn_count_past",
        "customer_amount_dev",
    ]
    nan_counts = dataset_a_features[a_engineered].isna().sum().to_dict()
    assert all(c == 0 for c in nan_counts.values()), f"Found NaNs in Dataset A engineered features: {nan_counts}"


def test_dataset_b_feature_schema(dataset_b_features):
    """Verify Dataset B required scenario features exist."""
    expected_cols = [
        "rolling_txn_15m",
        "rolling_fraud_rate_15m",
        "baseline_txn_15m",
        "baseline_fraud_rate",
        "velocity_ratio",
        "fraud_rate_deviation",
        "amount_deviation",
    ]

    for col in expected_cols:
        assert col in dataset_b_features.columns, f"Missing required scenario feature: {col}"


def test_dataset_b_no_infinite_values(dataset_b_features):
    """Verify Dataset B features contain zero infinite values."""
    num_cols = dataset_b_features.select_dtypes(include=[np.number]).columns
    inf_count = np.isinf(dataset_b_features[num_cols]).sum().sum()
    assert inf_count == 0, f"Found {inf_count} infinite values in Dataset B features!"


def test_dataset_b_features_no_nans(dataset_b_features):
    """Verify engineered numerical features in Dataset B have zero NaNs."""
    b_engineered = [
        "rolling_txn_15m",
        "rolling_fraud_rate_15m",
        "baseline_txn_15m",
        "baseline_fraud_rate",
        "velocity_ratio",
        "fraud_rate_deviation",
        "amount_deviation",
    ]
    nan_counts = dataset_b_features[b_engineered].isna().sum().to_dict()
    assert all(c == 0 for c in nan_counts.values()), f"Found NaNs in Dataset B engineered features: {nan_counts}"
