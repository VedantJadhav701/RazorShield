"""
test_merchant_state.py
----------------------
Unit tests for MerchantStateManager and SingleMerchantState.
Verifies chronological state updates, non-leakage, first transaction handling,
empty state, and unknown merchant handling.
"""

from datetime import datetime, timedelta
import pytest
from src.risk_engine.merchant_state import MerchantStateManager, SingleMerchantState


def test_empty_and_unknown_merchant_handling():
    manager = MerchantStateManager()
    state = manager.get_state("M_UNKNOWN_999")
    assert isinstance(state, SingleMerchantState)
    assert state.merchant_id == "M_UNKNOWN_999"
    assert state.transaction_count == 0
    assert state.velocity_ratio == 1.0


def test_first_transaction_handling():
    manager = MerchantStateManager()
    now = datetime(2026, 1, 1, 12, 0, 0)
    feats = manager.update_merchant(
        merchant_id="M_001",
        event_time=now,
        amount=150.0,
        calibrated_fraud_prob=0.02,
    )
    assert manager.get_state("M_001").transaction_count == 1
    assert feats["rolling_txn_15m"] == 1.0
    assert feats["amount_deviation"] >= 0.0


def test_chronological_state_updates_no_future_leakage():
    manager = MerchantStateManager()
    base_time = datetime(2026, 1, 1, 12, 0, 0)

    # 10 transactions 1 minute apart
    for i in range(10):
        t = base_time + timedelta(minutes=i)
        feats = manager.update_merchant("M_002", t, amount=100.0, calibrated_fraud_prob=0.05)
        assert feats["rolling_txn_15m"] == float(i + 1)

    # Transaction 30 minutes later should evict transactions outside 15m window
    t_later = base_time + timedelta(minutes=30)
    feats_later = manager.update_merchant("M_002", t_later, amount=200.0, calibrated_fraud_prob=0.10)
    assert feats_later["rolling_txn_15m"] == 1.0
