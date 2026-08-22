"""
fallback.py
-----------
Deterministic template-based fallback system for RazorShield explanation layer.

Activated when:
  - Model is unavailable / failed to load
  - Model inference times out
  - Model produces invalid JSON or schema errors
  - Model output fails deterministic grounding validation

Ensures 100% reliable execution with zero ungrounded claims or decision overrides.
"""

from __future__ import annotations

from src.explanation.schemas import ExplanationInput, ExplanationOutput


class DeterministicFallbackExplainer:
    """Template-based fallback explanation generator."""

    @staticmethod
    def generate_fallback_explanation(
        input_data: ExplanationInput,
        failure_reason: str = "Model fallback activated",
    ) -> ExplanationOutput:
        """
        Generates a 100% grounded template explanation matching ExplanationOutput schema.
        """
        state = input_data.incident_state
        severity = input_data.severity
        score = input_data.incident_score
        windows = input_data.suspicious_windows
        fe_ratio = input_data.fraud_excess_ratio
        vel_ratio = input_data.velocity_ratio
        camp_active = input_data.campaign_active
        q = (input_data.user_question or "").strip().lower()

        # Title
        if q:
            title = f"RAZOR AI Risk Analysis ({input_data.merchant_id})"
        else:
            title = f"RazorShield Defensive Risk Assessment: {state} ({severity} Severity)"

        # Campaign context string
        if camp_active:
            camp_ctx = (
                f"A promotional campaign is currently active for merchant {input_data.merchant_id}. "
                f"Volume velocity ({vel_ratio:.1f}x baseline) is normalized, but fraud excess ({fe_ratio:.1f}x baseline) remains actionable."
            )
        else:
            camp_ctx = (
                f"No promotional campaign is active for merchant {input_data.merchant_id}. "
                f"Observed volume velocity is {vel_ratio:.1f}x baseline."
            )

        # Base action
        if state == "ALERT":
            action = "Initiate immediate merchant review, enforce step-up authentication, and review high-risk transaction batches."
        elif state == "INVESTIGATE":
            action = "Monitor merchant temporal stream closely and apply selective verification on suspicious transactions."
        else:
            action = "Maintain standard automated processing."

        # Dynamic Question-Specific Summary
        if "driver" in q or "main risk" in q or "primary risk" in q:
            summary = (
                f"The primary risk drivers for merchant {input_data.merchant_id} are the Fraud Excess Ratio ({fe_ratio:.1f}x baseline) "
                f"and Spike Probability ({input_data.spike_probability * 100:.1f}%). "
                f"The policy engine calculated an incident score of {score:.2f} across {windows} suspicious monitoring windows."
            )
        elif "flag" in q or "analyst" in q or "review" in q or "should" in q:
            if state in ["ALERT", "INVESTIGATE"]:
                summary = (
                    f"Yes, an analyst should review merchant {input_data.merchant_id} because the system is in {state} state ({severity} severity) "
                    f"with {windows} suspicious windows detected. Recommended action: {action}"
                )
            else:
                summary = (
                    f"No immediate manual flagging is required for merchant {input_data.merchant_id}. "
                    f"The merchant is currently in NORMAL state (policy score {score:.2f}, {windows} suspicious windows). "
                    f"Recommended action: {action}"
                )
        elif "campaign" in q or "flash sale" in q or "normalization" in q or "how" in q:
            summary = (
                f"Flash sale campaign normalization adjusts volume velocity thresholds during registered promotional events. "
                f"This prevents legitimate traffic spikes from triggering false-positive fraud alerts. "
                f"For merchant {input_data.merchant_id}, campaign status is currently {'ACTIVE' if camp_active else 'INACTIVE'}."
            )
        elif q:
            summary = (
                f"Addressing your query regarding '{input_data.user_question}': Merchant {input_data.merchant_id} is currently evaluated as {state} "
                f"({severity} severity, policy score {score:.2f}). Observed fraud excess ratio is {fe_ratio:.1f}x baseline and volume velocity is {vel_ratio:.1f}x baseline."
            )
        elif state == "ALERT":
            summary = (
                f"RazorShield classified merchant {input_data.merchant_id} activity as {state} ({severity} severity, policy score {score:.2f}) "
                f"because a fraud anomaly persisted across {windows} consecutive monitoring windows. "
                f"The estimated fraud excess ratio is {fe_ratio:.1f}x baseline with a volume velocity of {vel_ratio:.1f}x baseline. "
                f"{camp_ctx}"
            )
        elif state == "INVESTIGATE":
            summary = (
                f"RazorShield flagged merchant {input_data.merchant_id} activity for {state} ({severity} severity, policy score {score:.2f}) "
                f"due to a detected anomaly in {windows} monitoring window. "
                f"The fraud excess ratio is {fe_ratio:.1f}x baseline and volume velocity is {vel_ratio:.1f}x baseline. "
                f"{camp_ctx}"
            )
        else:  # NORMAL
            summary = (
                f"RazorShield evaluated merchant {input_data.merchant_id} activity as {state} ({severity} severity, policy score {score:.2f}). "
                f"Observed fraud excess ratio is {fe_ratio:.1f}x baseline and volume velocity is {vel_ratio:.1f}x baseline. "
                f"{camp_ctx}"
            )

        # Key signals
        key_signals = [
            f"Policy Incident Score: {score:.2f}",
            f"Fraud Excess Ratio: {fe_ratio:.1f}x baseline",
            f"Volume Velocity Ratio: {vel_ratio:.1f}x baseline",
            f"Consecutive Suspicious Windows: {windows}",
        ]

        confidence_note = (
            f"Explanation generated via deterministic fallback ({failure_reason}). "
            f"Decision ({state}) is authoritatively determined by RazorShield policy engine."
        )

        return ExplanationOutput(
            title=title,
            summary=summary,
            key_signals=key_signals,
            campaign_context=camp_ctx,
            recommended_action=action,
            confidence_note=confidence_note,
        )
