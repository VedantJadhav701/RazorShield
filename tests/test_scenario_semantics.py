"""
test_scenario_semantics.py
---------------------------
Unit tests verifying semantic contract behavior for Dataset B scenarios.
"""

from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def scenario_summary():
    path = DATA_DIR / "dataset_b_scenario_summary.parquet"
    if not path.exists():
        pytest.skip(f"Scenario summary file not found: {path}")
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def audit_json():
    path = DATA_DIR / "dataset_b_audit.json"
    if not path.exists():
        pytest.skip(f"Audit JSON not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_scenario_counts_and_types(scenario_summary):
    """Verify that Dataset B contains 60 scenarios and all 4 scenario types."""
    assert len(scenario_summary) == 60, f"Expected 60 scenarios, got {len(scenario_summary)}"
    expected_types = {"normal", "fraud_spike", "volume_only_spike", "amount_shift"}
    actual_types = set(scenario_summary["scenario_type"].unique())
    assert expected_types == actual_types, f"Missing scenario types! Expected {expected_types}, got {actual_types}"


def test_all_scenarios_pass_semantic_contract(scenario_summary):
    """Verify all scenarios pass their intended semantic verification contract."""
    failed = scenario_summary[~scenario_summary["semantic_pass"]]
    assert len(failed) == 0, f"{len(failed)} scenarios failed semantic contract:\n{failed[['scenario_id', 'scenario_type', 'semantic_notes']]}"


def test_normal_scenarios_semantics(scenario_summary):
    """Verify normal scenarios have low fraud rate change and zero fraud_spike label."""
    normals = scenario_summary[scenario_summary["scenario_type"] == "normal"]
    assert len(normals) > 0
    assert (normals["fraud_spike_label"] == 0).all()
    assert (normals["fraud_rate_diff"] < 0.05).all()


def test_fraud_spike_scenarios_semantics(scenario_summary):
    """Verify fraud_spike scenarios have material fraud rate increase and fraud_spike label == 1."""
    spikes = scenario_summary[scenario_summary["scenario_type"] == "fraud_spike"]
    assert len(spikes) > 0
    assert (spikes["fraud_spike_label"] == 1).all()
    assert (spikes["fraud_rate_diff"] >= 0.03).all()


def test_volume_only_hard_negatives(scenario_summary):
    """Verify volume_only_spike hard negatives have high volume multiplier but low fraud rate."""
    vols = scenario_summary[scenario_summary["scenario_type"] == "volume_only_spike"]
    assert len(vols) > 0
    assert (vols["fraud_spike_label"] == 0).all()
    assert (vols["volume_multiplier"] >= 1.3).all()
    assert (vols["fraud_rate_diff"] < 0.05).all()


def test_amount_shift_hard_negatives(scenario_summary):
    """Verify amount_shift hard negatives have high amount shift but low fraud rate."""
    amts = scenario_summary[scenario_summary["scenario_type"] == "amount_shift"]
    assert len(amts) > 0
    assert (amts["fraud_spike_label"] == 0).all()
    assert (amts["amount_shift"] >= 1.3).all()
    assert (amts["fraud_rate_diff"] < 0.05).all()


def test_audit_json_zero_failures(audit_json):
    """Verify dataset_b_audit.json records zero overall semantic failures."""
    assert audit_json["overall_semantic_fail_count"] == 0
    assert audit_json["overall_semantic_pass_count"] == 60
    assert len(audit_json["failed_scenarios"]) == 0
