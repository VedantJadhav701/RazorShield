"""
policies.py
-----------
Configurable policy engine and threshold routing for RazorShield risk engine.

Operating Modes:
  - CONSERVATIVE: Low thresholds for early verification/alerting.
  - BALANCED: Standard balanced thresholds derived from Phase 4 validation.
  - HIGH_SENSITIVITY: Ultra-sensitive fraud monitoring.

Note:
  "The combined risk score is a policy score, not a calibrated probability."
"""

from __future__ import annotations

from typing import Any, Literal
from src.risk_engine.schemas import RiskDecision, RiskSignal, TransactionInput


class PolicyEngine:
    """Configurable risk policy engine."""

    POLICY_CONFIGS = {
        "CONSERVATIVE": {
            "threshold_verify": 0.10,
            "threshold_alert": 0.30,
            "w_txn": 0.50,
            "w_spike": 0.50,
        },
        "BALANCED": {
            "threshold_verify": 0.20,
            "threshold_alert": 0.50,
            "w_txn": 0.50,
            "w_spike": 0.50,
        },
        "HIGH_SENSITIVITY": {
            "threshold_verify": 0.05,
            "threshold_alert": 0.15,
            "w_txn": 0.40,
            "w_spike": 0.60,
        },
    }

    def __init__(self, mode: str = "BALANCED", cost_fp: float = 1.0, cost_fn: float = 10.0):
        self.mode = mode.upper() if mode.upper() in self.POLICY_CONFIGS else "BALANCED"
        self.config = self.POLICY_CONFIGS[self.mode]
        self.cost_fp = cost_fp
        self.cost_fn = cost_fn

    def calculate_combined_risk_score(
        self,
        calibrated_fraud_prob: float,
        spike_prob: float,
    ) -> float:
        """
        Calculates combined risk score.
        "The combined risk score is a policy score, not a calibrated probability."
        """
        w_txn = self.config["w_txn"]
        w_spike = self.config["w_spike"]
        score = (w_txn * calibrated_fraud_prob) + (w_spike * spike_prob)
        return float(min(1.0, max(0.0, score)))

    def evaluate_decision(
        self,
        tx: TransactionInput,
        calibrated_fraud_prob: float,
        spike_prob: float,
        feature_dict: dict[str, float],
        campaign_active: bool = False,
    ) -> RiskDecision:
        """
        Evaluates decision routing (APPROVE / VERIFY / ALERT) and generates structured evidence.
        """
        combined_score = self.calculate_combined_risk_score(calibrated_fraud_prob, spike_prob)
        t_verify = self.config["threshold_verify"]
        t_alert = self.config["threshold_alert"]

        # Decision routing
        if combined_score >= t_alert:
            decision: Literal["APPROVE", "VERIFY", "ALERT"] = "ALERT"
            severity: Literal["LOW", "MEDIUM", "HIGH"] = "HIGH"
        elif combined_score >= t_verify:
            decision = "VERIFY"
            severity = "MEDIUM"
        else:
            decision = "APPROVE"
            severity = "LOW"

        # Structured evidence signals
        signals = []

        # 1. Calibrated transaction probability signal
        if calibrated_fraud_prob >= 0.50:
            signals.append(
                RiskSignal(name="calibrated_fraud_probability", value=round(calibrated_fraud_prob, 4), direction="elevated")
            )

        # 2. Fraud excess ratio signal
        fraud_excess = feature_dict.get("fraud_excess_ratio", 1.0)
        if fraud_excess >= 2.0:
            signals.append(
                RiskSignal(name="fraud_excess_ratio", value=round(fraud_excess, 2), direction="elevated")
            )

        # 3. Velocity ratio signal
        velocity = feature_dict.get("velocity_ratio", 1.0)
        if velocity >= 2.0:
            dir_str = "suppressed" if campaign_active else "elevated"
            signals.append(
                RiskSignal(name="velocity_ratio", value=round(velocity, 2), direction=dir_str)
            )

        # 4. Amount deviation signal
        amt_dev = feature_dict.get("amount_deviation", 1.0)
        if amt_dev >= 3.0:
            signals.append(
                RiskSignal(name="amount_deviation", value=round(amt_dev, 2), direction="elevated")
            )

        # 5. Spike probability signal
        if spike_prob >= 0.40:
            signals.append(
                RiskSignal(name="spike_probability", value=round(spike_prob, 4), direction="elevated")
            )

        return RiskDecision(
            transaction_id=tx.transaction_id,
            merchant_id=tx.merchant_id,
            event_time=tx.event_time,
            calibrated_fraud_probability=round(calibrated_fraud_prob, 4),
            spike_probability=round(spike_prob, 4),
            combined_risk_score=round(combined_score, 4),
            decision=decision,
            severity=severity,
            signals=signals,
            campaign_active=campaign_active,
            policy_mode=self.mode,
        )
