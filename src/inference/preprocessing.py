"""
preprocessing.py
----------------
Data cleaning and validation helpers for incoming API transaction payloads.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from src.api.schemas import TransactionApiInput

LOGGER = logging.getLogger("inference-preprocessing")


def validate_raw_api_payload(payload: dict[str, Any]) -> TransactionApiInput:
    """
    Validates and cleans incoming raw API request dictionary.
    Raises ValueError if required fields are missing or invalid.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid request payload: Must be a JSON object.")

    # Amount check
    amount = payload.get("amount")
    if amount is None or not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError(f"Invalid transaction amount: {amount}. Amount must be a non-negative float.")

    # Event time check
    event_time_raw = payload.get("event_time")
    if isinstance(event_time_raw, str):
        try:
            event_time = datetime.fromisoformat(event_time_raw.replace("Z", "+00:00"))
        except Exception:
            raise ValueError(f"Malformed event_time timestamp: '{event_time_raw}'. Must be ISO 8601 format.")
    elif isinstance(event_time_raw, datetime):
        event_time = event_time_raw
    else:
        raise ValueError("Missing or invalid 'event_time' timestamp.")

    merchant_id = payload.get("merchant_id")
    transaction_id = payload.get("transaction_id")

    if not merchant_id or not str(merchant_id).strip():
        raise ValueError("Missing required field 'merchant_id'.")
    if not transaction_id or not str(transaction_id).strip():
        raise ValueError("Missing required field 'transaction_id'.")

    return TransactionApiInput(
        merchant_id=str(merchant_id).strip(),
        transaction_id=str(transaction_id).strip(),
        customer_id=str(payload.get("customer_id", "C_UNKNOWN")).strip(),
        device_id=str(payload.get("device_id", "D_UNKNOWN")).strip(),
        event_time=event_time,
        amount=float(amount),
        payment_method=str(payload.get("payment_method", "card")).lower().strip(),
        transaction_type=str(payload.get("transaction_type", "sale")).lower().strip(),
        policy_mode=str(payload.get("policy_mode", "BALANCED")).upper().strip(),
    )
