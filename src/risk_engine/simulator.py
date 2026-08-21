"""
simulator.py
------------
Real-time transaction-stream replay simulator for RazorShield Risk Engine.

Replays Dataset B test scenarios chronologically, tracks execution latency per transaction,
records decisions without using ground-truth during processing, and computes evaluation metrics.

Outputs:
  - data/processed/risk_simulation_results.parquet
  - data/processed/risk_simulation_summary.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any

import numpy as np
import pandas as pd

from src.risk_engine.campaign import CampaignRegistration
from src.risk_engine.decision_engine import RiskDecisionEngine
from src.risk_engine.schemas import TransactionInput

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("risk-simulator")


class TransactionSimulator:
    """Replays transaction streams and records risk decisions."""

    def __init__(self, policy_mode: str = "BALANCED"):
        self.engine = RiskDecisionEngine(policy_mode=policy_mode)
        self.policy_mode = policy_mode

    def run_simulation(
        self,
        dataset_b_path: Path | None = None,
        register_demo_campaigns: bool = True,
    ) -> dict[str, Any]:
        if dataset_b_path is None:
            dataset_b_path = PROCESSED_DIR / "dataset_b_features.parquet"

        LOGGER.info("Loading Dataset B test scenarios for simulation from %s ...", dataset_b_path)
        df_b = pd.read_parquet(dataset_b_path)
        test_df = df_b[df_b["split"] == "test"].copy()

        # Sort strictly chronologically by event_time across test scenarios
        test_df = test_df.sort_values("event_time").reset_index(drop=True)

        if register_demo_campaigns:
            # Register campaign for volume_only_spike test merchants
            vol_merchants = test_df[test_df["scenario_type"] == "volume_only_spike"]["merchant_id"].unique()
            for m_id in vol_merchants:
                m_txs = test_df[test_df["merchant_id"] == m_id]
                min_t = m_txs["event_time"].min()
                max_t = m_txs["event_time"].max()
                self.engine.register_campaign(
                    CampaignRegistration(
                        merchant_id=m_id,
                        campaign_name="FLASH_SALE_PROMO",
                        start_time=min_t,
                        end_time=max_t,
                        expected_volume_multiplier=4.0,
                    )
                )

        LOGGER.info("Replaying %d test transactions chronologically ...", len(test_df))

        results = []
        latencies_ms = []

        for idx, row in test_df.iterrows():
            tx_input = TransactionInput(
                transaction_id=str(row["transaction_id"]),
                merchant_id=str(row["merchant_id"]),
                customer_id=str(row.get("customer_id", "C_UNKNOWN")),
                device_id=str(row.get("device_id", "D_UNKNOWN")),
                event_time=row["event_time"],
                amount=float(row["amount"]),
                payment_method=str(row.get("payment_method", "card")),
                transaction_type=str(row.get("transaction_type", "sale")),
            )

            pred_prob = float(row.get("predicted_fraud_prob", 0.01))

            t_start = time.perf_counter()
            decision = self.engine.process_transaction(tx_input, calibrated_fraud_prob=pred_prob)
            t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            latencies_ms.append(t_elapsed_ms)

            # Ground truth is accessed ONLY for offline evaluation storage
            is_fraud = int(row.get("is_fraud", 0))
            fraud_spike = int(row.get("fraud_spike", 0))
            is_alert_or_verify = 1 if decision.decision in ["VERIFY", "ALERT"] else 0

            # Classification error flags
            is_false_positive = 1 if (is_alert_or_verify == 1 and fraud_spike == 0) else 0
            is_false_negative = 1 if (is_alert_or_verify == 0 and fraud_spike == 1) else 0

            # Extract merchant state signals
            m_state = self.engine.state_manager.get_state(tx_input.merchant_id)

            results.append({
                "transaction_id": decision.transaction_id,
                "scenario_id": str(row["scenario_id"]),
                "scenario_type": str(row["scenario_type"]),
                "merchant_id": decision.merchant_id,
                "event_time": decision.event_time,
                "calibrated_fraud_probability": decision.calibrated_fraud_probability,
                "spike_probability": decision.spike_probability,
                "combined_risk_score": decision.combined_risk_score,
                "velocity_ratio": m_state.velocity_ratio,
                "fraud_excess_ratio": m_state.fraud_excess_ratio,
                "amount_deviation": m_state.amount_deviation,
                "campaign_active": decision.campaign_active,
                "decision": decision.decision,
                "severity": decision.severity,
                "is_fraud": is_fraud,
                "fraud_spike": fraud_spike,
                "is_false_positive": is_false_positive,
                "is_false_negative": is_false_negative,
                "latency_ms": round(t_elapsed_ms, 4),
            })

        sim_df = pd.DataFrame(results)
        parquet_path = PROCESSED_DIR / "risk_simulation_results.parquet"
        sim_df.to_parquet(parquet_path, index=False)
        LOGGER.info("Simulation results saved to %s", parquet_path)

        # Calculate metrics
        avg_latency = float(np.mean(latencies_ms))
        p99_latency = float(np.percentile(latencies_ms, 99))

        by_scenario = {}
        for stype, grp in sim_df.groupby("scenario_type"):
            total_n = len(grp)
            alerts = int((grp["decision"].isin(["VERIFY", "ALERT"])).sum())
            if stype == "fraud_spike":
                actual_spikes = int((grp["fraud_spike"] == 1).sum())
                detected_spikes = int(((grp["decision"].isin(["VERIFY", "ALERT"])) & (grp["fraud_spike"] == 1)).sum())
                rec = detected_spikes / max(1, actual_spikes)
                prec = detected_spikes / max(1, alerts)
                by_scenario[stype] = {
                    "scenario_type": stype,
                    "total_transactions": total_n,
                    "actual_spike_rows": actual_spikes,
                    "detected_spikes": detected_spikes,
                    "fraud_spike_recall": round(rec, 4),
                    "fraud_spike_precision": round(prec, 4),
                    "false_alert_rate": round((alerts - detected_spikes) / total_n, 4),
                }
            else:
                by_scenario[stype] = {
                    "scenario_type": stype,
                    "total_transactions": total_n,
                    "false_alert_count": alerts,
                    "false_alert_rate": round(alerts / total_n, 4),
                }

        summary = {
            "total_simulated_transactions": len(sim_df),
            "policy_mode": self.policy_mode,
            "average_latency_ms": round(avg_latency, 4),
            "p99_latency_ms": round(p99_latency, 4),
            "decision_distribution": sim_df["decision"].value_counts().to_dict(),
            "scenario_evaluations": by_scenario,
        }

        json_path = PROCESSED_DIR / "risk_simulation_summary.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        LOGGER.info("Simulation summary saved to %s", json_path)
        return summary


if __name__ == "__main__":
    sim = TransactionSimulator(policy_mode="BALANCED")
    sim.run_simulation()
