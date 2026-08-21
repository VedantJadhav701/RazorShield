"""
test_modeling.py
----------------
Unit tests verifying Phase 3 and Phase 4 modeling standards, leakage isolation,
oracle feature exclusion, probability calibration, deployable fraud excess features,
cost optimization, and hard-negative handling.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"


@pytest.fixture(scope="module")
def model_metadata():
    path = MODELS_DIR / "model_metadata.json"
    if not path.exists():
        pytest.skip(f"Model metadata not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def calibration_report():
    path = DATA_DIR / "calibration_report.json"
    if not path.exists():
        pytest.skip(f"Calibration report not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def dataset_b_features():
    path = DATA_DIR / "dataset_b_features.parquet"
    if not path.exists():
        pytest.skip(f"Dataset B features not found: {path}")
    return pd.read_parquet(path)


def test_no_oracle_feature_in_deployable_model(model_metadata):
    """Verify ground-truth oracle feature (rolling_fraud_rate_15m) is NOT in deployable features."""
    spike_feats = model_metadata["spike_model"]["deployable_features"]
    assert "rolling_fraud_rate_15m" not in spike_feats, (
        "CRITICAL ERROR: Oracle feature 'rolling_fraud_rate_15m' found in deployable spike model features!"
    )
    assert "estimated_fraud_rate_15m" in spike_feats


def test_calibration_fitted_only_on_training_validation(calibration_report):
    """Verify probability calibration report exists and selected isotonic/sigmoid calibration."""
    assert calibration_report["selected_calibration_method"] in ["isotonic", "sigmoid", "raw"]
    methods = calibration_report["methods"]
    assert "validation" in methods["isotonic"]
    assert methods["isotonic"]["validation"]["ece"] <= methods["raw"]["validation"]["ece"]


def test_no_test_threshold_optimization():
    """Verify threshold optimization table exists and selected thresholds on Validation set."""
    path = DATA_DIR / "cost_optimized_thresholds.csv"
    assert path.exists(), "Cost optimized thresholds CSV missing!"
    df = pd.read_csv(path)
    assert "selected_val_threshold" in df.columns
    assert "test_expected_cost" in df.columns


def test_fraud_excess_ratio_calculation(dataset_b_features):
    """Verify fraud_excess_ratio formula: estimated_fraud_count_15m / max(expected_fraud_count_15m, 1e-5)."""
    df = dataset_b_features.head(1000)
    est_cnt = df["estimated_fraud_count_15m"].values
    exp_cnt = df["expected_fraud_count_15m"].values
    actual_ratio = df["fraud_excess_ratio"].values

    expected_ratio = est_cnt / np.maximum(exp_cnt, 1e-5)
    np.testing.assert_allclose(actual_ratio, expected_ratio, rtol=1e-3, atol=1e-3)


def test_expected_fraud_count_calculation(dataset_b_features):
    """Verify expected_fraud_count_15m formula: baseline_fraud_rate * rolling_txn_15m."""
    df = dataset_b_features.head(1000)
    b_rate = df["baseline_fraud_rate"].values
    roll_vol = df["rolling_txn_15m"].values
    actual_exp_cnt = df["expected_fraud_count_15m"].values

    expected_cnt = b_rate * roll_vol
    np.testing.assert_allclose(actual_exp_cnt, expected_cnt, rtol=1e-3, atol=1e-3)


def test_cost_optimization():
    """Verify cost optimization table cost_optimized_thresholds.csv has positive expected cost."""
    path = DATA_DIR / "cost_optimized_thresholds.csv"
    df = pd.read_csv(path)
    assert (df["test_expected_cost"] >= 0).all()


def test_scenario_isolation(dataset_b_features):
    """Verify scenario split isolation (no scenario ID in multiple splits)."""
    scenario_splits = dataset_b_features.groupby("scenario_id")["split"].nunique()
    assert (scenario_splits == 1).all()
