"""
test_incident_campaign.py
-------------------------
Unit tests verifying campaign behavior on merchant incident detection.
Ensures volume-only spikes (flash sales) remain non-alerting while fraud spikes
during campaigns STILL trigger persistent incident alerts.
"""

from datetime import datetime
import pytest
from src.incident.incident_policy import IncidentPolicyEngine
from src.incident.incident_state import MerchantIncidentState


def test_volume_only_spike_remains_non_alerting_during_campaign():
    state = MerchantIncidentState("M_FLASH_SALE")
    state.update_window(
        window_time=datetime(2026, 1, 1, 12, 0),
        spike_prob=0.10,
        fraud_excess_ratio=1.0,  # Normal fraud excess despite high velocity
        velocity_ratio=4.5,
        suspicious_tx_count=0,
        estimated_fraud_cnt=0.05,
        expected_fraud_cnt=0.05,
        campaign_active=True,
    )

    policy = IncidentPolicyEngine(mode="BALANCED", persistence_n=2)
    eval_res = policy.evaluate_incident_state(state)
    assert eval_res["incident_state"] == "NORMAL"


def test_fraud_spike_during_campaign_triggers_alert():
    state = MerchantIncidentState("M_CAMPAIGN_ATTACK")
    now = datetime(2026, 1, 1, 12, 0)

    # Window 1: High velocity AND high fraud excess during campaign
    state.update_window(now, 0.40, 3.5, 4.5, 3, 0.40, 0.10, campaign_active=True)
    # Window 2: Continued high fraud excess
    state.update_window(now, 0.45, 4.0, 4.5, 4, 0.50, 0.10, campaign_active=True)

    policy = IncidentPolicyEngine(mode="BALANCED", persistence_n=2)
    eval_res = policy.evaluate_incident_state(state)
    assert eval_res["incident_state"] == "ALERT"
    assert eval_res["campaign_active"] is True
