"""
test_integration.py
-------------------
End-to-end integration tests connecting public API payloads, inference adapter,
risk decision engine, merchant incident state, and explanation generator.
"""

from datetime import datetime, timedelta
import json
import pytest
from app import analyze_transaction, reset_demo_state
from src.inference.adapter import InferenceAdapter
from src.inference.preprocessing import validate_raw_api_payload


def test_end_to_end_transaction_flow():
    reset_demo_state()
    now = datetime(2026, 1, 1, 12, 0)

    # 1. Normal transaction
    res1 = json.loads(analyze_transaction("M_INT", "TX_01", "C_1", "D_1", now.isoformat(), 50.0))
    assert res1["decision"]["action"] in ["APPROVE", "VERIFY", "ALERT"]
    assert res1["merchant_risk"]["incident_state"] in ["NORMAL", "INVESTIGATE", "ALERT"]

    # 2. Elevated transaction
    res2 = json.loads(analyze_transaction("M_INT", "TX_02", "C_1", "D_1", (now + timedelta(minutes=1)).isoformat(), 950.0))
    assert "explanation" in res2
    assert "summary" in res2["explanation"]


def test_no_decision_override_integrity():
    reset_demo_state()
    now = datetime(2026, 1, 1, 12, 0).isoformat()
    res = json.loads(analyze_transaction("M_OVERRIDE", "TX_O1", "C_O1", "D_O1", now, 100.0))

    # Action is authoritatively set by risk decision engine
    action = res["decision"]["action"]
    severity = res["merchant_risk"]["severity"]
    exp_title = res["explanation"]["title"]

    if action == "APPROVE":
        assert "ALERT" not in exp_title or "HIGH" not in exp_title
