"""
incident_engine.py
------------------
RazorShield Merchant Incident Engine orchestrator.

Sits above the transaction risk engine and evaluates persistent merchant-level fraud incidents.
Distinguishes single isolated suspicious transactions from persistent merchant-level fraud attacks.

Outputs structured JSON evidence without free-form LLM text.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any

from src.incident.incident_policy import IncidentPolicyEngine
from src.incident.incident_state import MerchantIncidentState
from src.risk_engine.decision_engine import RiskDecisionEngine
from src.risk_engine.schemas import CampaignRegistration, RiskDecision, TransactionInput

ROOT = Path(__file__).resolve().parents[2]
LOGGER = logging.getLogger("merchant-incident-engine")


class MerchantIncidentEngine:
    """Merchant Incident Detection Engine orchestrator."""

    def __init__(
        self,
        policy_mode: str = "BALANCED",
        persistence_n: int = 2,
        models_dir: Path | None = None,
    ):
        self.risk_engine = RiskDecisionEngine(policy_mode=policy_mode, models_dir=models_dir)
        self.policy_engine = IncidentPolicyEngine(mode=policy_mode, persistence_n=persistence_n)
        self.incident_states: dict[str, MerchantIncidentState] = {}
        self.last_window_time: dict[str, datetime] = {}
        self.window_suspicious_tx_counts: dict[str, int] = {}

    def get_incident_state(self, merchant_id: str) -> MerchantIncidentState:
        if merchant_id not in self.incident_states:
            self.incident_states[merchant_id] = MerchantIncidentState(merchant_id)
        return self.incident_states[merchant_id]

    def register_campaign(self, campaign: CampaignRegistration):
        """Registers a merchant promotional campaign."""
        self.risk_engine.register_campaign(campaign)

    def process_transaction(
        self,
        tx: TransactionInput,
        calibrated_fraud_prob: float | None = None,
    ) -> tuple[RiskDecision, dict[str, Any]]:
        """
        Processes a transaction through both the risk decision engine and the merchant incident layer.
        Returns (tx_decision, incident_decision_json).
        """
        # 1. Transaction Risk Engine evaluation
        tx_decision = self.risk_engine.process_transaction(
            tx=tx,
            calibrated_fraud_prob=calibrated_fraud_prob,
        )

        merchant_id = tx.merchant_id
        event_time = tx.event_time

        # Track suspicious transactions in current 1-minute window
        is_suspicious_tx = 1 if (tx_decision.combined_risk_score >= 0.20 or tx_decision.calibrated_fraud_probability >= 0.30) else 0
        self.window_suspicious_tx_counts[merchant_id] = (
            self.window_suspicious_tx_counts.get(merchant_id, 0) + is_suspicious_tx
        )

        # Update window state when time moves into a new minute bucket or on first transaction
        curr_min_bucket = event_time.replace(second=0, microsecond=0)
        last_min_bucket = self.last_window_time.get(merchant_id)

        inc_state = self.get_incident_state(merchant_id)
        m_state = self.risk_engine.state_manager.get_state(merchant_id)

        if last_min_bucket is None or curr_min_bucket > last_min_bucket:
            self.last_window_time[merchant_id] = curr_min_bucket
            self.window_suspicious_tx_counts[merchant_id] = is_suspicious_tx

        # Update window state with latest rolling metrics
        inc_state.update_window(
            window_time=event_time,
            spike_prob=tx_decision.spike_probability,
            fraud_excess_ratio=m_state.fraud_excess_ratio,
            velocity_ratio=m_state.velocity_ratio,
            suspicious_tx_count=self.window_suspicious_tx_counts.get(merchant_id, 0),
            estimated_fraud_cnt=m_state.calibrated_estimated_fraud_count,
            expected_fraud_cnt=m_state.expected_fraud_count,
            campaign_active=tx_decision.campaign_active,
            spike_threshold=0.15,
            excess_threshold=1.2,
        )

        # 2. Evaluate Merchant Incident Policy
        incident_eval = self.policy_engine.evaluate_incident_state(inc_state)
        return tx_decision, incident_eval

    def reset_state(self):
        """Resets risk engine and merchant incident states."""
        self.risk_engine.reset_state()
        self.incident_states.clear()
        self.last_window_time.clear()
        self.window_suspicious_tx_counts.clear()
