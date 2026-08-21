"""
incident_policy.py
------------------
Configurable persistence, policy score, and incident state routing.

Incident States:
  - NORMAL: No meaningful persistent anomaly.
  - INVESTIGATE: Suspicious anomaly detected, persistence insufficient for full alert.
  - ALERT: Persistent and materially elevated merchant fraud incident.

Note:
  "The incident score is a policy score, not a calibrated probability."
"""

from __future__ import annotations

from typing import Any, Literal
from src.incident.incident_state import MerchantIncidentState


class IncidentPolicyEngine:
    """Configurable merchant incident policy engine."""

    POLICY_CONFIGS = {
        "CONSERVATIVE": {
            "min_consecutive_windows_for_alert": 1,
            "threshold_investigate": 0.25,
            "threshold_alert": 0.50,
            "w_spike": 0.40,
            "w_excess": 0.40,
            "w_persist": 0.20,
        },
        "BALANCED": {
            "min_consecutive_windows_for_alert": 2,
            "threshold_investigate": 0.35,
            "threshold_alert": 0.65,
            "w_spike": 0.40,
            "w_excess": 0.40,
            "w_persist": 0.20,
        },
        "HIGH_SENSITIVITY": {
            "min_consecutive_windows_for_alert": 1,
            "threshold_investigate": 0.20,
            "threshold_alert": 0.45,
            "w_spike": 0.35,
            "w_excess": 0.45,
            "w_persist": 0.20,
        },
    }

    def __init__(self, mode: str = "BALANCED", persistence_n: int = 2):
        self.mode = mode.upper() if mode.upper() in self.POLICY_CONFIGS else "BALANCED"
        self.config = self.POLICY_CONFIGS[self.mode].copy()
        self.config["min_consecutive_windows_for_alert"] = persistence_n

    def calculate_incident_score(
        self,
        state: MerchantIncidentState,
    ) -> float:
        """
        Calculates merchant incident policy score.
        "The incident score is a policy score, not a calibrated probability."
        """
        w_spike = self.config["w_spike"]
        w_excess = self.config["w_excess"]
        w_persist = self.config["w_persist"]

        n_req = self.config["min_consecutive_windows_for_alert"]
        excess_norm = min(1.0, max(0.0, state.current_fraud_excess_ratio / 8.0))
        persist_norm = min(1.0, max(0.0, state.consecutive_suspicious_windows / max(1, n_req)))

        score = (
            (w_spike * state.current_spike_probability)
            + (w_excess * excess_norm)
            + (w_persist * persist_norm)
        )

        return float(min(1.0, max(0.0, score)))

    def evaluate_incident_state(
        self,
        state: MerchantIncidentState,
    ) -> dict[str, Any]:
        """
        Evaluates merchant incident state (NORMAL / INVESTIGATE / ALERT) and generates evidence signals.
        """
        incident_score = self.calculate_incident_score(state)
        n_req = self.config["min_consecutive_windows_for_alert"]
        t_inv = self.config["threshold_investigate"]
        t_alert = self.config["threshold_alert"]

        # Incident State Routing
        if state.consecutive_suspicious_windows >= n_req or incident_score >= t_alert:
            incident_state: Literal["NORMAL", "INVESTIGATE", "ALERT"] = "ALERT"
            severity: Literal["LOW", "MEDIUM", "HIGH"] = "HIGH"
        elif state.consecutive_suspicious_windows >= 1 or incident_score >= t_inv:
            incident_state = "INVESTIGATE"
            severity = "MEDIUM"
        else:
            incident_state = "NORMAL"
            severity = "LOW"

        # Signals for structured explainability JSON
        signals = []

        if state.current_spike_probability >= 0.35:
            signals.append({
                "name": "spike_probability",
                "value": round(state.current_spike_probability, 4),
                "direction": "elevated"
            })

        if state.current_fraud_excess_ratio >= 1.8:
            signals.append({
                "name": "fraud_excess_ratio",
                "value": round(state.current_fraud_excess_ratio, 2),
                "direction": "elevated"
            })

        if state.current_velocity_ratio >= 2.0:
            dir_str = "suppressed" if state.campaign_active else "elevated"
            signals.append({
                "name": "velocity_ratio",
                "value": round(state.current_velocity_ratio, 2),
                "direction": dir_str
            })

        if state.consecutive_suspicious_windows >= 1:
            signals.append({
                "name": "consecutive_suspicious_windows",
                "value": state.consecutive_suspicious_windows,
                "direction": "persistent" if state.consecutive_suspicious_windows >= n_req else "elevated"
            })

        return {
            "merchant_id": state.merchant_id,
            "incident_state": incident_state,
            "severity": severity,
            "incident_score": round(incident_score, 4),
            "spike_probability": round(state.current_spike_probability, 4),
            "fraud_excess_ratio": round(state.current_fraud_excess_ratio, 2),
            "velocity_ratio": round(state.current_velocity_ratio, 2),
            "suspicious_windows": state.consecutive_suspicious_windows,
            "total_suspicious_windows": state.total_suspicious_windows,
            "campaign_active": state.campaign_active,
            "policy_mode": self.mode,
            "signals": signals,
        }
