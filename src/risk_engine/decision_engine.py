"""
decision_engine.py
------------------
RazorShield Risk Decision Engine core orchestrator.

Loads pre-trained calibrated transaction models and Phase 4 deployable spike models.
Executes real-time transaction risk evaluation with structured evidence output.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.risk_engine.campaign import CampaignManager
from src.risk_engine.merchant_state import MerchantStateManager
from src.risk_engine.policies import PolicyEngine
from src.risk_engine.schemas import CampaignRegistration, RiskDecision, TransactionInput

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"

LOGGER = logging.getLogger("risk-decision-engine")

NUMERIC_FEATURES_TX = [
    "amount", "amount_log1p", "hour", "day_of_week", "is_weekend",
    "customer_txn_count_past", "customer_amount_mean_past", "customer_amount_std_past",
    "device_txn_count_past", "customer_amount_dev", "identity_available",
    "missing_p_email", "missing_r_email", "missing_addr1", "missing_device_info"
]

CATEGORICAL_FEATURES_TX = [
    "ProductCD", "card1", "card2", "card3", "card4", "card5", "card6",
    "addr1", "addr2", "P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"
]

PHASE4_SPIKE_FEATURES = [
    "rolling_txn_15m",
    "baseline_txn_15m",
    "velocity_ratio",
    "estimated_fraud_rate_15m",
    "baseline_fraud_rate",
    "estimated_fraud_rate_deviation",
    "amount_deviation",
    "fraud_signal_ratio",
    "estimated_fraud_count_15m",
    "expected_fraud_count_15m",
    "fraud_excess_ratio",
    "volume_deviation",
    "fraud_excess_minus_velocity",
    "amount_shift_indicator",
]


class RiskDecisionEngine:
    """Core deterministic risk decision engine."""

    def __init__(
        self,
        policy_mode: str = "BALANCED",
        models_dir: Path | None = None,
    ):
        if models_dir is None:
            models_dir = MODELS_DIR

        self.models_dir = models_dir
        self.state_manager = MerchantStateManager()
        self.campaign_manager = CampaignManager()
        self.policy_engine = PolicyEngine(mode=policy_mode)

        self._load_models()

    def _load_models(self):
        """Loads trained transaction, calibration, and spike model artifacts."""
        tx_path = self.models_dir / "transaction_model" / "xgboost_model.joblib"
        enc_path = self.models_dir / "transaction_model" / "encoder.joblib"
        cal_path = self.models_dir / "transaction_model" / "calibrated_model.joblib"
        spike_path = self.models_dir / "spike_model" / "xgboost_spike_model_v2.joblib"

        if not tx_path.exists() or not spike_path.exists():
            raise FileNotFoundError("Required model artifacts missing from models directory.")

        self.tx_model = joblib.load(tx_path)
        self.tx_encoder = joblib.load(enc_path)
        self.cal_model = joblib.load(cal_path) if cal_path.exists() else None
        self.spike_model = joblib.load(spike_path)

    def _predict_calibrated_fraud_prob(self, tx: TransactionInput) -> float:
        """Predicts calibrated transaction-level fraud probability P(fraud | transaction)."""
        hour = tx.event_time.hour
        day_of_week = tx.event_time.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        amount_log1p = float(np.log1p(max(0.0, tx.amount)))

        # Historical proxies from merchant state
        m_state = self.state_manager.get_state(tx.merchant_id)
        cust_past_cnt = max(0, m_state.transaction_count - 1)
        cust_mean_past = m_state.baseline_amount
        cust_std_past = 0.0
        dev_past_cnt = max(0, m_state.transaction_count - 1)
        cust_dev = float(tx.amount / max(1.0, cust_mean_past))

        num_vals = [
            tx.amount, amount_log1p, hour, day_of_week, is_weekend,
            cust_past_cnt, cust_mean_past, cust_std_past,
            dev_past_cnt, cust_dev, 1, 0, 0, 0, 0
        ]

        cat_vals = [["unknown"] * len(CATEGORICAL_FEATURES_TX)]
        cat_encoded = self.tx_encoder.transform(cat_vals)

        X_tx = np.hstack([np.array(num_vals, dtype=np.float32).reshape(1, -1), cat_encoded.astype(np.float32)])
        raw_prob = float(self.tx_model.predict_proba(X_tx)[0, 1])

        if self.cal_model is not None:
            if hasattr(self.cal_model, "transform"):
                cal_prob = float(self.cal_model.transform(np.array([raw_prob]))[0])
            else:
                cal_prob = float(self.cal_model.predict_proba(np.array([[raw_prob]]))[0, 1])
        else:
            cal_prob = raw_prob

        return float(min(1.0, max(0.0, cal_prob)))

    def register_campaign(self, campaign: CampaignRegistration):
        """Registers a merchant promotional campaign."""
        self.campaign_manager.register_campaign(campaign)

    def process_transaction(
        self,
        tx: TransactionInput,
        calibrated_fraud_prob: float | None = None,
    ) -> RiskDecision:
        """
        Processes a single transaction through the risk decision pipeline.
        Returns a RiskDecision object with structured evidence.
        """
        # 1. Calibrated transaction model
        if calibrated_fraud_prob is None:
            cal_prob = self._predict_calibrated_fraud_prob(tx)
        else:
            cal_prob = float(min(1.0, max(0.0, calibrated_fraud_prob)))

        # 2. Chronological merchant state update
        feature_dict = self.state_manager.update_merchant(
            merchant_id=tx.merchant_id,
            event_time=tx.event_time,
            amount=tx.amount,
            calibrated_fraud_prob=cal_prob,
        )

        # 3. Campaign check
        is_active, vol_mult = self.campaign_manager.is_campaign_active(tx.merchant_id, tx.event_time)
        adj_features = self.campaign_manager.adjust_features_for_campaign(
            feature_dict, is_active, vol_mult
        )

        # 4. Spike model prediction using deployable features ONLY
        X_spike = np.array(
            [[adj_features[f] for f in PHASE4_SPIKE_FEATURES]], dtype=np.float32
        )
        spike_prob = float(self.spike_model.predict_proba(X_spike)[0, 1])
        spike_prob = float(min(1.0, max(0.0, spike_prob)))

        # 5. Policy evaluation & structured evidence generation
        decision = self.policy_engine.evaluate_decision(
            tx=tx,
            calibrated_fraud_prob=cal_prob,
            spike_prob=spike_prob,
            feature_dict=adj_features,
            campaign_active=is_active,
        )

        return decision

    def reset_state(self):
        """Resets merchant states and campaigns."""
        self.state_manager.reset()
        self.campaign_manager.clear()
