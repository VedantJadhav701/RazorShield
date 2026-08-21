"""
test_explanation_grounding.py
------------------------------
Adversarial unit tests for GroundingValidator.
Verifies rejection of contradictory numbers, unsupported claims, and ungrounded statements.
"""

import pytest
from src.explanation.schemas import ExplanationInput, ExplanationOutput
from src.explanation.validator import GroundingValidator


def test_adversarial_case2_contradictory_fraud_excess_ratio():
    validator = GroundingValidator()
    inp = ExplanationInput(
        merchant_id="M_ADV",
        incident_state="ALERT",
        severity="HIGH",
        incident_score=0.85,
        spike_probability=0.90,
        fraud_excess_ratio=8.2,
        velocity_ratio=4.1,
        suspicious_windows=3,
        campaign_active=False,
    )
    # Output claims fraud excess ratio is 3.2 instead of 8.2
    out = ExplanationOutput(
        title="Alert Explanation",
        summary="RazorShield detected an anomaly where fraud excess ratio is 3.2 and velocity is 4.1.",
        key_signals=["Fraud Excess: 3.2"],
        campaign_context="No campaign",
        recommended_action="Review",
        confidence_note="Authoritative decision",
    )
    val = validator.validate_grounding(inp, out)
    # MUST FAIL numeric grounding!
    assert val["numeric_grounded"] is False
    assert val["passed"] is False


def test_adversarial_case5_unsupported_monetary_amount():
    validator = GroundingValidator()
    inp = ExplanationInput(
        merchant_id="M_ADV",
        incident_state="ALERT",
        severity="HIGH",
        incident_score=0.85,
        spike_probability=0.90,
        fraud_excess_ratio=8.2,
        velocity_ratio=4.1,
        suspicious_windows=3,
        campaign_active=False,
    )
    # Output claims $50,000 in fraudulent transactions when no monetary amount is in evidence
    out = ExplanationOutput(
        title="Alert Explanation",
        summary="RazorShield detected $50,000 in fraudulent transactions across 3 monitoring windows.",
        key_signals=["Fraud Excess: 8.2"],
        campaign_context="No campaign",
        recommended_action="Review",
        confidence_note="Authoritative decision",
    )
    val = validator.validate_grounding(inp, out)
    # MUST FAIL hallucination check!
    assert val["hallucination_detected"] is True
    assert val["passed"] is False
