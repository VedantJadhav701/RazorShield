"""
test_leakage.py
---------------
Unit tests verifying strict temporal leakage prevention and chronological ordering.
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


def test_chronological_ordering(dataset_a_features):
    """Verify Dataset A is strictly sorted chronologically."""
    assert dataset_a_features["event_time"].is_monotonic_increasing, (
        "Dataset A event_time is not strictly monotonic increasing!"
    )


def test_train_val_test_boundaries(dataset_a_features):
    """Verify chronological split boundaries for Dataset A."""
    df = dataset_a_features
    train_max = df[df["split"] == "train"]["event_time"].max()
    val_min = df[df["split"] == "validation"]["event_time"].min()
    val_max = df[df["split"] == "validation"]["event_time"].max()
    test_min = df[df["split"] == "test"]["event_time"].min()

    assert train_max <= val_min, f"Train max ({train_max}) > Val min ({val_min})"
    assert val_max <= test_min, f"Val max ({val_max}) > Test min ({test_min})"


def test_customer_past_count_leakage(dataset_a_features):
    """
    Verify customer_txn_count_past for row i equals the count of prior
    transactions for that customer strictly before row i.
    """
    df = dataset_a_features.head(5000)  # Check first 5k rows for speed
    
    # Check first occurrence of every customer has past_count == 0
    first_occurrences = df.groupby("customer_proxy_id")["customer_txn_count_past"].first()
    assert (first_occurrences == 0).all(), "First occurrence of customer has past_count > 0!"

    # Spot check sample customers
    sample_customers = df["customer_proxy_id"].value_counts().head(5).index
    for cust in sample_customers:
        cust_rows = df[df["customer_proxy_id"] == cust].copy()
        expected_counts = np.arange(len(cust_rows))
        actual_counts = cust_rows["customer_txn_count_past"].values
        np.testing.assert_array_equal(
            actual_counts,
            expected_counts,
            err_msg=f"Leakage detected in customer_txn_count_past for customer {cust}!"
        )


def test_customer_past_amount_mean_leakage(dataset_a_features):
    """
    Verify customer_amount_mean_past for row i excludes current amount and uses
    only past amounts strictly before index i.
    """
    df = dataset_a_features.head(5000)
    sample_customers = df["customer_proxy_id"].value_counts()[lambda x: x >= 3].head(5).index

    for cust in sample_customers:
        cust_rows = df[df["customer_proxy_id"] == cust].copy()
        amounts = cust_rows["amount"].values
        actual_means = cust_rows["customer_amount_mean_past"].values

        for idx in range(len(cust_rows)):
            if idx == 0:
                assert actual_means[idx] == 0.0, "First transaction past mean must be 0!"
            else:
                expected_mean = np.mean(amounts[:idx])
                np.testing.assert_almost_equal(
                    actual_means[idx],
                    expected_mean,
                    decimal=3,
                    err_msg=f"Customer amount mean leakage at index {idx} for customer {cust}!"
                )


def test_scenario_split_integrity(dataset_b_features):
    """
    Verify scenario-level split integrity for Dataset B (each scenario belongs
    strictly to 1 split).
    """
    scenario_splits = dataset_b_features.groupby("scenario_id")["split"].nunique()
    leaked_scenarios = scenario_splits[scenario_splits > 1]
    assert len(leaked_scenarios) == 0, f"Scenario leakage detected across splits: {leaked_scenarios.to_dict()}"
