"""
test_incident_persistence.py
-----------------------------
Unit tests for Merchant Incident persistence logic and state resets.
"""

from datetime import datetime, timedelta
import pytest
from src.incident.incident_policy import IncidentPolicyEngine
from src.incident.incident_state import MerchantIncidentState


def test_single_suspicious_transaction_does_not_create_alert():
    state = MerchantIncidentState("M_SINGLE")
    state.update_window(
        window_time=datetime(2026, 1, 1, 12, 0),
        spike_prob=0.40,
        fraud_excess_ratio=2.0,
        velocity_ratio=1.5,
        suspicious_tx_count=1,
        estimated_fraud_cnt=0.20,
        expected_fraud_cnt=0.10,
    )
    # Window count is 1
    assert state.consecutive_suspicious_windows == 1

    policy = IncidentPolicyEngine(mode="BALANCED", persistence_n=2)
    eval_res = policy.evaluate_incident_state(state)
    # 1 window is INVESTIGATE, NOT ALERT!
    assert eval_res["incident_state"] == "INVESTIGATE"
    assert eval_res["severity"] == "MEDIUM"


def test_persistence_n_creates_alert():
    state = MerchantIncidentState("M_PERSIST")
    now = datetime(2026, 1, 1, 12, 0)

    # Window 1
    state.update_window(now, 0.40, 2.5, 1.5, 2, 0.30, 0.10)
    assert state.consecutive_suspicious_windows == 1

    # Window 2
    state.update_window(now + timedelta(minutes=1), 0.45, 3.0, 1.8, 3, 0.40, 0.10)
    assert state.consecutive_suspicious_windows == 2

    policy = IncidentPolicyEngine(mode="BALANCED", persistence_n=2)
    eval_res = policy.evaluate_incident_state(state)
    # 2 consecutive windows -> ALERT!
    assert eval_res["incident_state"] == "ALERT"
    assert eval_res["severity"] == "HIGH"


def test_persistence_resets_after_normal_window():
    state = MerchantIncidentState("M_RESET")
    now = datetime(2026, 1, 1, 12, 0)

    # Window 1 (Suspicious)
    state.update_window(now, 0.40, 2.5, 1.5, 2, 0.30, 0.10)
    assert state.consecutive_suspicious_windows == 1

    # Window 2 (Normal)
    state.update_window(now + timedelta(minutes=1), 0.05, 0.8, 1.0, 0, 0.01, 0.10)
    assert state.consecutive_suspicious_windows == 0

    policy = IncidentPolicyEngine(mode="BALANCED", persistence_n=2)
    eval_res = policy.evaluate_incident_state(state)
    assert eval_res["incident_state"] == "NORMAL"
