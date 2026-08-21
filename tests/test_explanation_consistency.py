"""
test_explanation_consistency.py
--------------------------------
Adversarial unit tests for decision, severity, and campaign consistency.
"""

import pytest
from src.explanation.schemas import ExplanationInput, ExplanationOutput
from src.explanation.validator import GroundingValidator


def test_adversarial_case1_investigate_claimed_as_confirmed_fraud():
    validator = GroundingValidator()
    inp = ExplanationInput(
        merchant_id="M_ADV",
        incident_state="INVESTIGATE",
        severity="MEDIUM",
        incident_score=0.45,
        spike_probability=0.40,
        fraud_excess_ratio=2.1,
        velocity_ratio=1.8,
        suspicious_windows=1,
        campaign_active=False,
    )
    out = ExplanationOutput(
        title="Investigation Explanation",
        summary="RazorShield verified this confirmed fraud incident for merchant M_ADV.",
        key_signals=["Fraud Excess: 2.1x"],
        campaign_context="No campaign",
        recommended_action="Monitor",
        confidence_note="Authoritative decision",
    )
    val = validator.validate_grounding(inp, out)
    assert val["decision_consistent"] is False
    assert val["passed"] is False


def test_adversarial_case3_active_campaign_claimed_inactive():
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
        campaign_active=True,
    )
    out = ExplanationOutput(
        title="Alert Explanation",
        summary="RazorShield detected elevated fraud excess 8.2x. No promotional campaign is active.",
        key_signals=["Fraud Excess: 8.2x"],
        campaign_context="No campaign active for merchant",
        recommended_action="Review",
        confidence_note="Authoritative decision",
    )
    val = validator.validate_grounding(inp, out)
    assert val["campaign_consistent"] is False
    assert val["passed"] is False


def test_adversarial_case4_high_severity_claimed_as_low_risk():
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
    out = ExplanationOutput(
        title="Alert Explanation",
        summary="RazorShield evaluated this low risk activity for merchant M_ADV.",
        key_signals=["Fraud Excess: 8.2x"],
        campaign_context="No campaign",
        recommended_action="Review",
        confidence_note="Authoritative decision",
    )
    val = validator.validate_grounding(inp, out)
    assert val["severity_consistent"] is False
    assert val["passed"] is False
