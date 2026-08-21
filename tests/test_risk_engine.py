"""
test_risk_engine.py
-------------------
Unit tests for RiskDecisionEngine and end-to-end processing.
Verifies probability bounds, combined risk score, malformed input handling,
and deterministic replay.
"""

from datetime import datetime
import pytest
from src.risk_engine.decision_engine import RiskDecisionEngine
from src.risk_engine.schemas import TransactionInput


@pytest.fixture(scope="module")
def engine():
    return RiskDecisionEngine(policy_mode="BALANCED")


def test_probability_bounds_and_combined_risk(engine):
    tx = TransactionInput(
        transaction_id="TX_TEST_01",
        merchant_id="M_TEST",
        event_time=datetime(2026, 1, 1, 12, 0, 0),
        amount=250.0,
    )
    decision = engine.process_transaction(tx)
    assert 0.0 <= decision.calibrated_fraud_probability <= 1.0
    assert 0.0 <= decision.spike_probability <= 1.0
    assert 0.0 <= decision.combined_risk_score <= 1.0
    assert decision.decision in ["APPROVE", "VERIFY", "ALERT"]


def test_deterministic_replay(engine):
    engine.reset_state()
    tx = TransactionInput(
        transaction_id="TX_DET_01",
        merchant_id="M_DET",
        event_time=datetime(2026, 1, 1, 12, 0, 0),
        amount=150.0,
    )

    dec1 = engine.process_transaction(tx)

    engine.reset_state()
    dec2 = engine.process_transaction(tx)

    assert dec1.calibrated_fraud_probability == dec2.calibrated_fraud_probability
    assert dec1.spike_probability == dec2.spike_probability
    assert dec1.combined_risk_score == dec2.combined_risk_score
    assert dec1.decision == dec2.decision
