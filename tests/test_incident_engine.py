"""
test_incident_engine.py
------------------------
Unit tests for MerchantIncidentEngine end-to-end processing, merchant isolation,
and deterministic incident state updates.
"""

from datetime import datetime
import pytest
from src.incident.incident_engine import MerchantIncidentEngine
from src.risk_engine.schemas import TransactionInput


@pytest.fixture
def incident_engine():
    return MerchantIncidentEngine(policy_mode="BALANCED", persistence_n=2)


def test_merchant_isolation(incident_engine):
    tx_a = TransactionInput(
        transaction_id="TX_A_01",
        merchant_id="MERCHANT_A",
        event_time=datetime(2026, 1, 1, 12, 0),
        amount=100.0,
    )
    tx_b = TransactionInput(
        transaction_id="TX_B_01",
        merchant_id="MERCHANT_B",
        event_time=datetime(2026, 1, 1, 12, 0),
        amount=500.0,
    )

    dec_a, inc_a = incident_engine.process_transaction(tx_a, calibrated_fraud_prob=0.01)
    dec_b, inc_b = incident_engine.process_transaction(tx_b, calibrated_fraud_prob=0.85)

    assert inc_a["merchant_id"] == "MERCHANT_A"
    assert inc_b["merchant_id"] == "MERCHANT_B"
    assert inc_a["incident_state"] != inc_b["incident_state"] or inc_a["incident_score"] != inc_b["incident_score"]


def test_deterministic_incident_state(incident_engine):
    tx = TransactionInput(
        transaction_id="TX_DET_INC",
        merchant_id="MERCHANT_DET",
        event_time=datetime(2026, 1, 1, 12, 0),
        amount=200.0,
    )

    incident_engine.reset_state()
    _, inc1 = incident_engine.process_transaction(tx, calibrated_fraud_prob=0.40)

    incident_engine.reset_state()
    _, inc2 = incident_engine.process_transaction(tx, calibrated_fraud_prob=0.40)

    assert inc1["incident_score"] == inc2["incident_score"]
    assert inc1["incident_state"] == inc2["incident_state"]
