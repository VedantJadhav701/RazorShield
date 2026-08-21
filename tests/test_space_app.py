"""
test_space_app.py
-----------------
Unit tests for app.py Gradio backend interface, API endpoints, scenario replay,
state resets, and schema validation.
"""

from datetime import datetime
import json
import pytest
from app import (
    analyze_merchant,
    analyze_transaction,
    explain_evidence,
    reset_demo_state,
    run_scenario,
)


def test_analyze_transaction_valid_request():
    reset_demo_state()
    raw_res = analyze_transaction(
        merchant_id="M_TEST_APP",
        transaction_id="TX_TEST_001",
        customer_id="C_101",
        device_id="D_101",
        event_time=datetime(2026, 1, 1, 12, 0).isoformat(),
        amount=150.0,
        payment_method="card",
        transaction_type="sale",
        policy_mode="BALANCED",
    )
    res = json.loads(raw_res)
    assert "transaction_risk" in res
    assert "merchant_risk" in res
    assert "explanation" in res
    assert "performance" in res
    assert res["transaction_id"] == "TX_TEST_001"
    assert res["merchant_id"] == "M_TEST_APP"


def test_analyze_transaction_validation_error():
    # Negative amount -> Validation Error
    raw_res = analyze_transaction(
        merchant_id="M_ERR",
        transaction_id="TX_ERR",
        amount=-50.0,
    )
    res = json.loads(raw_res)
    assert "error" in res
    assert res["error"] == "Validation Error"


def test_analyze_merchant_query():
    reset_demo_state()
    raw_res = analyze_merchant("M_QUERY_TEST")
    res = json.loads(raw_res)
    assert res["merchant_id"] == "M_QUERY_TEST"
    assert "rolling_window" in res
    assert "incident_state" in res


def test_scenario_replay():
    reset_demo_state()
    raw_res = run_scenario("FRAUD_SPIKE", "BALANCED")
    res = json.loads(raw_res)
    assert res["scenario_name"] == "FRAUD_SPIKE"
    assert "incident_state_distribution" in res
    assert "explanation" in res


def test_explain_evidence():
    ev = json.dumps({
        "merchant_id": "M_EV",
        "incident_state": "ALERT",
        "severity": "HIGH",
        "incident_score": 0.88,
        "spike_probability": 0.92,
        "fraud_excess_ratio": 8.2,
        "velocity_ratio": 4.1,
        "suspicious_windows": 3,
        "campaign_active": False,
        "policy_mode": "BALANCED",
    })
    raw_res = explain_evidence(ev)
    res = json.loads(raw_res)
    assert "explanation" in res
    assert "validation" in res


def test_reset_demo_state():
    res_str = reset_demo_state()
    res = json.loads(res_str)
    assert res["status"] == "SUCCESS"
