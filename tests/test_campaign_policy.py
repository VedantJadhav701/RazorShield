"""
test_campaign_policy.py
-----------------------
Unit tests for CampaignManager and PolicyEngine.
Verifies campaign registration, campaign volume adjustment, fraud evidence preservation,
and decision routing.
"""

from datetime import datetime
import pytest
from src.risk_engine.campaign import CampaignManager
from src.risk_engine.policies import PolicyEngine
from src.risk_engine.schemas import CampaignRegistration, TransactionInput


def test_campaign_registration_and_active_check():
    mgr = CampaignManager()
    start = datetime(2026, 1, 1, 10, 0)
    end = datetime(2026, 1, 1, 14, 0)

    mgr.register_campaign(
        CampaignRegistration(
            merchant_id="M_102",
            campaign_name="FLASH_SALE",
            start_time=start,
            end_time=end,
            expected_volume_multiplier=4.5,
        )
    )

    active_t = datetime(2026, 1, 1, 11, 30)
    inactive_t = datetime(2026, 1, 1, 16, 0)

    is_act, mult = mgr.is_campaign_active("M_102", active_t)
    assert is_act is True
    assert mult == 4.5

    is_act_off, mult_off = mgr.is_campaign_active("M_102", inactive_t)
    assert is_act_off is False
    assert mult_off == 1.0


def test_campaign_does_not_suppress_fraud_evidence():
    mgr = CampaignManager()
    raw_feats = {
        "velocity_ratio": 4.5,
        "fraud_excess_ratio": 8.0,
        "estimated_fraud_rate_15m": 0.15,
    }

    adj_feats = mgr.adjust_features_for_campaign(raw_feats, is_campaign_active=True, volume_multiplier=4.5)
    # Velocity is dampened
    assert adj_feats["velocity_ratio"] == 1.0
    # Fraud excess ratio is PRESERVED
    assert adj_feats["fraud_excess_ratio"] == 8.0


def test_policy_decision_routing():
    policy = PolicyEngine(mode="BALANCED")
    tx = TransactionInput(
        transaction_id="TX_001",
        merchant_id="M_001",
        event_time=datetime(2026, 1, 1, 12, 0),
        amount=100.0,
    )

    # Low risk -> APPROVE
    dec_low = policy.evaluate_decision(tx, calibrated_fraud_prob=0.01, spike_prob=0.05, feature_dict={})
    assert dec_low.decision == "APPROVE"
    assert dec_low.severity == "LOW"

    # Medium risk -> VERIFY
    dec_med = policy.evaluate_decision(tx, calibrated_fraud_prob=0.30, spike_prob=0.30, feature_dict={})
    assert dec_med.decision == "VERIFY"
    assert dec_med.severity == "MEDIUM"

    # High risk -> ALERT
    dec_high = policy.evaluate_decision(tx, calibrated_fraud_prob=0.80, spike_prob=0.85, feature_dict={})
    assert dec_high.decision == "ALERT"
    assert dec_high.severity == "HIGH"
