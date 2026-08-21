"""
schemas.py
----------
Pydantic data models for the RazorShield Risk Decision Engine.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    """Input transaction event for risk evaluation."""

    transaction_id: str = Field(..., description="Unique transaction ID")
    merchant_id: str = Field(..., description="Merchant ID")
    customer_id: str = Field(default="C_UNKNOWN", description="Customer ID proxy")
    device_id: str = Field(default="D_UNKNOWN", description="Device ID proxy")
    event_time: datetime = Field(..., description="Transaction timestamp")
    amount: float = Field(..., ge=0.0, description="Transaction monetary amount")
    payment_method: str = Field(default="card", description="Payment method used")
    transaction_type: str = Field(default="sale", description="Transaction type")


class CampaignRegistration(BaseModel):
    """Merchant promotional campaign registration."""

    merchant_id: str = Field(..., description="Merchant ID")
    campaign_name: str = Field(..., description="Campaign name (e.g. FLASH_SALE)")
    start_time: datetime = Field(..., description="Campaign start timestamp")
    end_time: datetime = Field(..., description="Campaign end timestamp")
    expected_volume_multiplier: float = Field(default=3.0, ge=1.0, description="Expected volume multiplier")


class RiskSignal(BaseModel):
    """Structured evidence signal for explainability."""

    name: str = Field(..., description="Signal feature name")
    value: float = Field(..., description="Signal numerical value")
    direction: Literal["elevated", "normal", "suppressed"] = Field(..., description="Signal status direction")


class RiskDecision(BaseModel):
    """Output decision object containing structured evidence."""

    transaction_id: str = Field(..., description="Transaction ID")
    merchant_id: str = Field(..., description="Merchant ID")
    event_time: datetime = Field(..., description="Transaction timestamp")
    calibrated_fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated transaction P(fraud)")
    spike_probability: float = Field(..., ge=0.0, le=1.0, description="Merchant fraud-spike probability")
    combined_risk_score: float = Field(..., ge=0.0, le=1.0, description="Policy combined risk score")
    decision: Literal["APPROVE", "VERIFY", "ALERT"] = Field(..., description="Action decision")
    severity: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Risk severity level")
    signals: list[RiskSignal] = Field(default_factory=list, description="Structured evidence signals")
    campaign_active: bool = Field(default=False, description="Whether merchant campaign is active")
    policy_mode: str = Field(default="BALANCED", description="Operating policy mode")
