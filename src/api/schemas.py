"""
schemas.py
----------
Pydantic schemas for RazorShield Public API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class TransactionApiInput(BaseModel):
    """Public API input payload for transaction risk analysis."""

    merchant_id: str = Field(..., description="Unique merchant identifier")
    transaction_id: str = Field(..., description="Unique transaction identifier")
    customer_id: str = Field(default="C_UNKNOWN", description="Customer identifier")
    device_id: str = Field(default="D_UNKNOWN", description="Device identifier")
    event_time: datetime = Field(..., description="Event timestamp (ISO 8601)")
    amount: float = Field(..., ge=0.0, description="Transaction amount (>= 0.0)")
    payment_method: str = Field(default="card", description="Payment method")
    transaction_type: str = Field(default="sale", description="Transaction type")
    policy_mode: str = Field(default="BALANCED", description="Policy mode (CONSERVATIVE, BALANCED, HIGH_SENSITIVITY)")

    @field_validator("merchant_id", "transaction_id")
    @classmethod
    def check_non_empty(cls, v: str, info: Any) -> str:
        if not v or not v.strip():
            raise ValueError(f"Field '{info.field_name}' must be a non-empty string.")
        return v.strip()


class TransactionRiskResponse(BaseModel):
    fraud_probability: float = Field(..., ge=0.0, le=1.0)


class MerchantRiskResponse(BaseModel):
    spike_probability: float = Field(..., ge=0.0, le=1.0)
    fraud_excess_ratio: float = Field(..., ge=0.0)
    velocity_ratio: float = Field(..., ge=0.0)
    incident_state: Literal["NORMAL", "INVESTIGATE", "ALERT"]
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    incident_score: float = Field(..., ge=0.0, le=1.0)
    suspicious_windows: int = Field(..., ge=0)


class CampaignInfoResponse(BaseModel):
    active: bool
    campaign_name: Optional[str] = None


class DecisionResponse(BaseModel):
    action: Literal["APPROVE", "VERIFY", "ALERT"]
    policy_mode: str


class PerformanceMetricsResponse(BaseModel):
    risk_engine_latency_ms: float = Field(..., ge=0.0)
    slm_latency_ms: float = Field(..., ge=0.0)
    total_latency_ms: float = Field(..., ge=0.0)


class AnalyzeTransactionResponse(BaseModel):
    """Complete structured JSON response for transaction analysis."""

    transaction_id: str
    merchant_id: str
    transaction_risk: TransactionRiskResponse
    merchant_risk: MerchantRiskResponse
    campaign: CampaignInfoResponse
    decision: DecisionResponse
    explanation: dict[str, Any]
    performance: PerformanceMetricsResponse
