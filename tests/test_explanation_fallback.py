"""
test_explanation_fallback.py
-----------------------------
Unit tests for DeterministicFallbackExplainer and automatic fallback execution in RazorShieldExplainer.
"""

import pytest
from src.explanation.explainer import RazorShieldExplainer
from src.explanation.fallback import DeterministicFallbackExplainer
from src.explanation.schemas import ExplanationInput


def test_deterministic_fallback_generator():
    inp = ExplanationInput(
        merchant_id="M_FALLBACK",
        incident_state="ALERT",
        severity="HIGH",
        incident_score=0.88,
        spike_probability=0.92,
        fraud_excess_ratio=8.2,
        velocity_ratio=4.1,
        suspicious_windows=3,
        campaign_active=True,
    )
    out = DeterministicFallbackExplainer.generate_fallback_explanation(inp, failure_reason="Test fallback")

    assert out.title == "RazorShield Defensive Risk Assessment: ALERT (HIGH Severity)"
    assert "8.2x baseline" in out.summary
    assert "M_FALLBACK" in out.summary
    assert "ALERT" in out.summary
    assert len(out.key_signals) == 4


def test_explainer_uses_fallback_when_model_unloaded():
    explainer = RazorShieldExplainer(model_loader=None)
    inp = ExplanationInput(
        merchant_id="M_TEST",
        incident_state="INVESTIGATE",
        severity="MEDIUM",
        incident_score=0.45,
        spike_probability=0.40,
        fraud_excess_ratio=2.1,
        velocity_ratio=1.8,
        suspicious_windows=1,
        campaign_active=False,
    )
    out, val_res = explainer.generate_explanation(inp)

    assert val_res["used_fallback"] is True
    assert val_res["passed"] is True
    assert out.title == "RazorShield Defensive Risk Assessment: INVESTIGATE (MEDIUM Severity)"
