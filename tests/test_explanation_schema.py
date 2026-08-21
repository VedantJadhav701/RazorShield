"""
test_explanation_schema.py
---------------------------
Unit tests for ExplanationInput, ExplanationOutput, and GoldExpectation schemas.
"""

import pytest
from src.explanation.schemas import ExplanationInput, ExplanationOutput, GoldExpectation


def test_explanation_input_schema():
    inp = ExplanationInput(
        merchant_id="M_101",
        incident_state="ALERT",
        severity="HIGH",
        incident_score=0.85,
        spike_probability=0.90,
        fraud_excess_ratio=8.2,
        velocity_ratio=4.1,
        suspicious_windows=3,
        campaign_active=True,
    )
    assert inp.merchant_id == "M_101"
    assert inp.incident_state == "ALERT"
    assert inp.severity == "HIGH"


def test_explanation_output_schema():
    out = ExplanationOutput(
        title="Alert Explanation",
        summary="RazorShield detected elevated fraud excess across monitoring windows.",
        key_signals=["Fraud Excess: 8.2x"],
        campaign_context="Promotional campaign active",
        recommended_action="Initiate review",
        confidence_note="Authoritative decision",
    )
    assert out.title == "Alert Explanation"
    assert len(out.key_signals) == 1
