"""
adapter.py
----------
Inference Adapter for RazorShield Risk Engine.

Converts public API transaction payloads into the exact feature representation
expected by the trained XGBoost transaction model without data leakage or retrained dependencies.
Handles historical customer/device state tracking and unknown categorical values safely.
"""

from __future__ import annotations

import logging
import math
from typing import Any
import numpy as np
import pandas as pd

from src.api.schemas import TransactionApiInput

LOGGER = logging.getLogger("inference-adapter")


class CustomerHistoryTracker:
    """In-memory historical customer & device state tracker for API streaming inference."""

    def __init__(self):
        self.customer_history: dict[str, dict[str, Any]] = {}
        self.device_history: dict[str, int] = {}

    def get_and_update_customer_stats(self, customer_id: str, amount: float) -> dict[str, float]:
        """Retrieves past stats for customer, then updates history chronologically."""
        if customer_id not in self.customer_history:
            past_stats = {
                "customer_txn_count_past": 0,
                "customer_amount_mean_past": 0.0,
                "customer_amount_std_past": 0.0,
                "customer_amount_dev": 1.0,
            }
            self.customer_history[customer_id] = {
                "count": 1,
                "sum": float(amount),
                "sum_sq": float(amount ** 2),
            }
            return past_stats

        c_data = self.customer_history[customer_id]
        count = c_data["count"]
        sum_amt = c_data["sum"]
        sum_sq = c_data["sum_sq"]

        mean_past = sum_amt / count
        var_past = max(0.0, (sum_sq / count) - (mean_past ** 2))
        std_past = math.sqrt(var_past)
        amt_dev = amount / (mean_past + 1e-5)

        past_stats = {
            "customer_txn_count_past": count,
            "customer_amount_mean_past": float(mean_past),
            "customer_amount_std_past": float(std_past),
            "customer_amount_dev": float(amt_dev),
        }

        # Update state with current transaction
        c_data["count"] += 1
        c_data["sum"] += float(amount)
        c_data["sum_sq"] += float(amount ** 2)

        return past_stats

    def get_and_update_device_stats(self, device_id: str) -> int:
        """Retrieves past device transaction count, then updates state."""
        past_count = self.device_history.get(device_id, 0)
        self.device_history[device_id] = past_count + 1
        return past_count

    def reset(self):
        """Resets tracker state."""
        self.customer_history.clear()
        self.device_history.clear()


class InferenceAdapter:
    """Adapts public API input transactions into model feature DataFrames."""

    def __init__(self, tracker: CustomerHistoryTracker | None = None):
        self.tracker = tracker if tracker is not None else CustomerHistoryTracker()

    def transform_transaction(self, tx: TransactionApiInput) -> pd.DataFrame:
        """
        Transforms a single TransactionApiInput into a 1-row feature DataFrame
        compatible with the trained XGBoost transaction model.
        """
        event_time = tx.event_time
        amount = tx.amount

        # Basic time features
        hour = event_time.hour
        day_of_week = event_time.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        amount_log1p = float(np.log1p(max(0.0, amount)))

        # Historical customer & device features
        cust_stats = self.tracker.get_and_update_customer_stats(tx.customer_id, amount)
        dev_count = self.tracker.get_and_update_device_stats(tx.device_id)

        # Missingness & identity indicators
        identity_available = 0 if tx.device_id in ["D_UNKNOWN", "", None] else 1
        missing_p_email = 0
        missing_r_email = 1
        missing_addr1 = 1
        missing_device_info = 0 if identity_available == 1 else 1

        feature_dict = {
            "amount": float(amount),
            "amount_log1p": amount_log1p,
            "hour": int(hour),
            "day_of_week": int(day_of_week),
            "is_weekend": int(is_weekend),
            "customer_txn_count_past": int(cust_stats["customer_txn_count_past"]),
            "customer_amount_mean_past": float(cust_stats["customer_amount_mean_past"]),
            "customer_amount_std_past": float(cust_stats["customer_amount_std_past"]),
            "customer_amount_dev": float(cust_stats["customer_amount_dev"]),
            "device_txn_count_past": int(dev_count),
            "identity_available": int(identity_available),
            "missing_p_email": int(missing_p_email),
            "missing_r_email": int(missing_r_email),
            "missing_addr1": int(missing_addr1),
            "missing_device_info": int(missing_device_info),
        }

        df_feat = pd.DataFrame([feature_dict])
        return df_feat
