"""
incident_state.py
------------------
Chronological merchant incident state tracking.

Maintains window-level persistent anomaly counters, suspicious window streaks,
and incident start timestamps without future lookahead.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


class MerchantIncidentState:
    """Persistent incident state for a single merchant."""

    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self.current_spike_probability: float = 0.0
        self.current_fraud_excess_ratio: float = 1.0
        self.current_velocity_ratio: float = 1.0
        self.suspicious_transaction_count: int = 0
        self.estimated_fraud_count: float = 0.0
        self.expected_fraud_count: float = 0.0
        self.consecutive_suspicious_windows: int = 0
        self.total_suspicious_windows: int = 0
        self.campaign_active: bool = False
        self.incident_start_time: datetime | None = None
        self.last_update_time: datetime | None = None

    def update_window(
        self,
        window_time: datetime,
        spike_prob: float,
        fraud_excess_ratio: float,
        velocity_ratio: float,
        suspicious_tx_count: int,
        estimated_fraud_cnt: float,
        expected_fraud_cnt: float,
        campaign_active: bool = False,
        spike_threshold: float = 0.20,
        excess_threshold: float = 1.2,
    ) -> MerchantIncidentState:
        """
        Updates window-level incident state chronologically.
        A window is suspicious if spike_prob >= spike_threshold and fraud_excess_ratio >= excess_threshold.
        """
        self.last_update_time = window_time
        self.current_spike_probability = float(spike_prob)
        self.current_fraud_excess_ratio = float(fraud_excess_ratio)
        self.current_velocity_ratio = float(velocity_ratio)
        self.suspicious_transaction_count = int(suspicious_tx_count)
        self.estimated_fraud_count = float(estimated_fraud_cnt)
        self.expected_fraud_count = float(expected_fraud_cnt)
        self.campaign_active = campaign_active

        is_suspicious_window = (
            spike_prob >= spike_threshold
            and fraud_excess_ratio >= excess_threshold
            and (suspicious_tx_count >= 1 or estimated_fraud_cnt >= 0.15)
        )

        if is_suspicious_window:
            self.consecutive_suspicious_windows += 1
            self.total_suspicious_windows += 1
            if self.incident_start_time is None:
                self.incident_start_time = window_time
        else:
            self.consecutive_suspicious_windows = 0
            self.incident_start_time = None

        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "merchant_id": self.merchant_id,
            "current_spike_probability": round(self.current_spike_probability, 4),
            "current_fraud_excess_ratio": round(self.current_fraud_excess_ratio, 2),
            "current_velocity_ratio": round(self.current_velocity_ratio, 2),
            "suspicious_transaction_count": self.suspicious_transaction_count,
            "estimated_fraud_count": round(self.estimated_fraud_count, 4),
            "expected_fraud_count": round(self.expected_fraud_count, 4),
            "consecutive_suspicious_windows": self.consecutive_suspicious_windows,
            "total_suspicious_windows": self.total_suspicious_windows,
            "campaign_active": self.campaign_active,
            "incident_start_time": self.incident_start_time.isoformat() if self.incident_start_time else None,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
        }
