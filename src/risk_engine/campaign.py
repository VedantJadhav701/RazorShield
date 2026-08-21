"""
campaign.py
-----------
Merchant promotional campaign registration and risk signal adjustment.

During a registered promotional campaign (e.g., FLASH_SALE):
  - Volume velocity expectations are adjusted by expected_volume_multiplier.
  - Fraud-excess evidence REMAINS ACTIVE.
  - High transaction fraud probabilities and elevated fraud-excess ratios STILL trigger VERIFY / ALERT.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from src.risk_engine.schemas import CampaignRegistration


class CampaignManager:
    """Manages active merchant promotional campaign registrations."""

    def __init__(self):
        self.campaigns: dict[str, list[CampaignRegistration]] = {}

    def register_campaign(self, campaign: CampaignRegistration):
        """Registers a new promotional campaign for a merchant."""
        if campaign.merchant_id not in self.campaigns:
            self.campaigns[campaign.merchant_id] = []
        self.campaigns[campaign.merchant_id].append(campaign)

    def is_campaign_active(self, merchant_id: str, event_time: datetime) -> tuple[bool, float]:
        """
        Checks if a campaign is active for the merchant at event_time.
        Returns (is_active, expected_volume_multiplier).
        """
        if merchant_id not in self.campaigns:
            return False, 1.0

        for cmp in self.campaigns[merchant_id]:
            if cmp.start_time <= event_time <= cmp.end_time:
                return True, cmp.expected_volume_multiplier

        return False, 1.0

    def adjust_features_for_campaign(
        self,
        features: dict[str, float],
        is_campaign_active: bool,
        volume_multiplier: float,
    ) -> dict[str, float]:
        """
        Adjusts velocity expectations during active campaigns while preserving fraud excess signals.
        """
        adj_features = features.copy()
        if is_campaign_active:
            # Dampen velocity ratio by expected campaign volume multiplier
            raw_velocity = adj_features.get("velocity_ratio", 1.0)
            adj_velocity = max(1.0, raw_velocity / max(1.0, volume_multiplier))
            adj_features["velocity_ratio"] = adj_velocity
            adj_features["volume_deviation"] = adj_velocity
            adj_features["fraud_excess_minus_velocity"] = (
                adj_features.get("fraud_excess_ratio", 1.0) - adj_velocity
            )

        return adj_features

    def clear(self):
        self.campaigns.clear()
