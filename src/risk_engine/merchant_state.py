"""
merchant_state.py
------------------
Chronological per-merchant rolling temporal state manager.
Maintains 15-minute rolling windows and baseline window statistics without lookahead leakage.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any


class SingleMerchantState:
    """Rolling temporal state for a single merchant."""

    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self.transaction_count: int = 0
        self.first_event_time: datetime | None = None
        self.history: deque[tuple[datetime, float, float]] = deque()

        # Baseline statistics (derived from initial non-spike window <= 30 mins)
        self.baseline_txn_15m: float = 15.0
        self.baseline_fraud_rate: float = 0.008
        self.baseline_amount: float = 100.0

        # Current rolling 15-minute statistics
        self.rolling_15m_volume: float = 0.0
        self.rolling_15m_amount: float = 0.0
        self.calibrated_estimated_fraud_count: float = 0.0
        self.estimated_fraud_rate: float = 0.0

        # Derived deployable features
        self.velocity_ratio: float = 1.0
        self.fraud_signal_ratio: float = 1.0
        self.expected_fraud_count: float = 0.0
        self.fraud_excess_ratio: float = 1.0
        self.amount_deviation: float = 1.0
        self.estimated_fraud_rate_deviation: float = 0.0
        self.fraud_excess_minus_velocity: float = 0.0

    def update(
        self,
        event_time: datetime,
        amount: float,
        calibrated_fraud_prob: float,
    ) -> dict[str, float]:
        """
        Updates merchant state chronologically with a new transaction observation.
        Returns the updated feature map.
        """
        self.transaction_count += 1
        if self.first_event_time is None:
            self.first_event_time = event_time

        self.history.append((event_time, float(amount), float(calibrated_fraud_prob)))

        # Evict transactions older than 60 minutes from history memory buffer
        cutoff_buffer = event_time - timedelta(minutes=60)
        while self.history and self.history[0][0] < cutoff_buffer:
            self.history.popleft()

        # 1. Rolling 15-minute window [event_time - 15m, event_time]
        cutoff_15m = event_time - timedelta(minutes=15)
        window_15m = [tx for tx in self.history if tx[0] >= cutoff_15m]

        self.rolling_15m_volume = float(len(window_15m))
        self.rolling_15m_amount = float(sum(tx[1] for tx in window_15m))
        self.calibrated_estimated_fraud_count = float(sum(tx[2] for tx in window_15m))
        self.estimated_fraud_rate = float(
            self.calibrated_estimated_fraud_count / max(1.0, self.rolling_15m_volume)
        )

        # 2. Update baseline statistics during early window (first 30 minutes)
        base_cutoff = self.first_event_time + timedelta(minutes=30)
        if event_time <= base_cutoff:
            base_window = [tx for tx in self.history if tx[0] <= base_cutoff]
            time_span_mins = max(1.0, (base_window[-1][0] - base_window[0][0]).total_seconds() / 60.0)
            avg_15m_vol = (len(base_window) / time_span_mins) * 15.0
            avg_fraud_rate = sum(tx[2] for tx in base_window) / max(1.0, len(base_window))
            avg_amt = sum(tx[1] for tx in base_window) / max(1.0, len(base_window))

            self.baseline_txn_15m = max(1.0, avg_15m_vol)
            self.baseline_fraud_rate = max(0.0001, avg_fraud_rate)
            self.baseline_amount = max(1.0, avg_amt)

        # 3. Compute derived deployable features
        self.velocity_ratio = float(self.rolling_15m_volume / max(1.0, self.baseline_txn_15m))
        self.fraud_signal_ratio = float(
            self.estimated_fraud_rate / max(1e-5, self.baseline_fraud_rate)
        )
        self.expected_fraud_count = float(self.baseline_fraud_rate * self.rolling_15m_volume)
        self.fraud_excess_ratio = float(
            self.calibrated_estimated_fraud_count / max(1e-5, self.expected_fraud_count)
        )
        self.amount_deviation = float(amount / max(1.0, self.baseline_amount))
        self.estimated_fraud_rate_deviation = float(
            self.estimated_fraud_rate - self.baseline_fraud_rate
        )
        self.fraud_excess_minus_velocity = float(self.fraud_excess_ratio - self.velocity_ratio)

        return self.get_feature_dict()

    def get_feature_dict(self) -> dict[str, float]:
        """Returns feature vector matching Phase 4 deployable spike model inputs."""
        return {
            "rolling_txn_15m": self.rolling_15m_volume,
            "baseline_txn_15m": self.baseline_txn_15m,
            "velocity_ratio": self.velocity_ratio,
            "estimated_fraud_rate_15m": self.estimated_fraud_rate,
            "baseline_fraud_rate": self.baseline_fraud_rate,
            "estimated_fraud_rate_deviation": self.estimated_fraud_rate_deviation,
            "amount_deviation": self.amount_deviation,
            "fraud_signal_ratio": self.fraud_signal_ratio,
            "estimated_fraud_count_15m": self.calibrated_estimated_fraud_count,
            "expected_fraud_count_15m": self.expected_fraud_count,
            "fraud_excess_ratio": self.fraud_excess_ratio,
            "volume_deviation": self.velocity_ratio,
            "fraud_excess_minus_velocity": self.fraud_excess_minus_velocity,
            "amount_shift_indicator": self.amount_deviation,
        }


class MerchantStateManager:
    """Manages state for multiple merchants concurrently."""

    def __init__(self):
        self.merchants: dict[str, SingleMerchantState] = defaultdict(
            lambda: SingleMerchantState("UNKNOWN")
        )

    def get_state(self, merchant_id: str) -> SingleMerchantState:
        if merchant_id not in self.merchants:
            self.merchants[merchant_id] = SingleMerchantState(merchant_id)
        return self.merchants[merchant_id]

    def update_merchant(
        self,
        merchant_id: str,
        event_time: datetime,
        amount: float,
        calibrated_fraud_prob: float,
    ) -> dict[str, float]:
        state = self.get_state(merchant_id)
        return state.update(event_time, amount, calibrated_fraud_prob)

    def reset(self):
        self.merchants.clear()
