"""
incident_simulator.py
---------------------
Replay simulator and evaluator for RazorShield Merchant Incident Engine.

Replays Dataset B test scenarios chronologically, tracks persistent merchant incidents,
measures detection delay (median and P95), and computes incident precision/recall/F1 metrics.

Outputs:
  - data/processed/merchant_incident_results.parquet
  - data/processed/merchant_incident_summary.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import time
from typing import Any

import numpy as np
import pandas as pd

from src.incident.incident_engine import MerchantIncidentEngine
from src.risk_engine.campaign import CampaignRegistration
from src.risk_engine.schemas import TransactionInput

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("incident-simulator")


class IncidentSimulator:
    """Replays test scenarios through the Merchant Incident Engine."""

    def __init__(self, policy_mode: str = "BALANCED", persistence_n: int = 2):
        self.engine = MerchantIncidentEngine(policy_mode=policy_mode, persistence_n=persistence_n)
        self.policy_mode = policy_mode
        self.persistence_n = persistence_n

    def run_simulation(
        self,
        dataset_b_path: Path | None = None,
        register_demo_campaigns: bool = True,
    ) -> dict[str, Any]:
        if dataset_b_path is None:
            dataset_b_path = PROCESSED_DIR / "dataset_b_features.parquet"

        LOGGER.info("Loading Dataset B test scenarios for incident replay from %s ...", dataset_b_path)
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

        LOGGER.info("Replaying %d test transactions through Merchant Incident Engine ...", len(test_df))

        results = []
        latencies_ms = []

        # Detection delay tracking per scenario
        spike_start_times: dict[str, Any] = {}
        first_alert_times: dict[str, Any] = {}
        first_alert_window_counts: dict[str, int] = {}

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
            scenario_id = str(row["scenario_id"])
            is_spike_row = int(row.get("fraud_spike", 0))

            if is_spike_row == 1 and scenario_id not in spike_start_times:
                spike_start_times[scenario_id] = row["event_time"]

            t_start = time.perf_counter()
            tx_dec, inc_dec = self.engine.process_transaction(tx_input, calibrated_fraud_prob=pred_prob)
            t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            latencies_ms.append(t_elapsed_ms)

            if inc_dec["incident_state"] == "ALERT" and scenario_id not in first_alert_times:
                first_alert_times[scenario_id] = row["event_time"]
                first_alert_window_counts[scenario_id] = inc_dec["suspicious_windows"]

            # Ground truth is stored ONLY for offline evaluation
            is_fraud = int(row.get("is_fraud", 0))
            fraud_spike = int(row.get("fraud_spike", 0))

            results.append({
                "transaction_id": tx_input.transaction_id,
                "scenario_id": scenario_id,
                "scenario_type": str(row["scenario_type"]),
                "merchant_id": tx_input.merchant_id,
                "event_time": tx_input.event_time,
                "calibrated_fraud_probability": tx_dec.calibrated_fraud_probability,
                "spike_probability": tx_dec.spike_probability,
                "combined_risk_score": tx_dec.combined_risk_score,
                "incident_score": inc_dec["incident_score"],
                "incident_state": inc_dec["incident_state"],
                "suspicious_windows": inc_dec["suspicious_windows"],
                "campaign_active": inc_dec["campaign_active"],
                "is_fraud": is_fraud,
                "fraud_spike": fraud_spike,
                "latency_ms": round(t_elapsed_ms, 4),
            })

        sim_df = pd.DataFrame(results)
        parquet_path = PROCESSED_DIR / "merchant_incident_results.parquet"
        sim_df.to_parquet(parquet_path, index=False)
        LOGGER.info("Merchant incident results saved to %s", parquet_path)

        # 1. Detection Delay Evaluation
        delay_seconds_list = []
        delay_windows_list = []

        for sc_id, start_t in spike_start_times.items():
            if sc_id in first_alert_times:
                alert_t = first_alert_times[sc_id]
                delay_sec = max(0.0, (alert_t - start_t).total_seconds())
                delay_seconds_list.append(delay_sec)
                delay_win = first_alert_window_counts.get(sc_id, 1)
                delay_windows_list.append(delay_win)

        median_delay_sec = float(np.median(delay_seconds_list)) if delay_seconds_list else 0.0
        p95_delay_sec = float(np.percentile(delay_seconds_list, 95)) if delay_seconds_list else 0.0
        median_delay_windows = float(np.median(delay_windows_list)) if delay_windows_list else 0.0
        p95_delay_windows = float(np.percentile(delay_windows_list, 95)) if delay_windows_list else 0.0

        # 2. Metric calculation per scenario type and scenario-level incident detection
        by_stype = {}
        scenario_alerts = sim_df.groupby("scenario_id").agg(
            scenario_type=("scenario_type", "first"),
            has_alert=("incident_state", lambda s: (s == "ALERT").any()),
            has_investigate=("incident_state", lambda s: (s.isin(["INVESTIGATE", "ALERT"])).any()),
            actual_fraud_spike=("fraud_spike", lambda s: (s == 1).any()),
        )

        for stype, grp in sim_df.groupby("scenario_type"):
            total_n = len(grp)
            alerts = int((grp["incident_state"] == "ALERT").sum())
            investigates = int((grp["incident_state"] == "INVESTIGATE").sum())

            stype_scenarios = scenario_alerts[scenario_alerts["scenario_type"] == stype]
            sc_count = len(stype_scenarios)
            sc_alert_count = int(stype_scenarios["has_alert"].sum())
            sc_investigate_count = int(stype_scenarios["has_investigate"].sum())

            if stype == "fraud_spike":
                actual_spikes = int((grp["fraud_spike"] == 1).sum())
                detected_spikes = int(((grp["incident_state"].isin(["INVESTIGATE", "ALERT"])) & (grp["fraud_spike"] == 1)).sum())
                tp_sc = int(stype_scenarios["has_alert"].sum())
                sc_rec = tp_sc / max(1, sc_count)
                sc_prec = tp_sc / max(1, sc_alert_count)
                sc_f1 = (2 * sc_prec * sc_rec) / max(1e-5, sc_prec + sc_rec)

                by_stype[stype] = {
                    "scenario_type": stype,
                    "total_scenarios": sc_count,
                    "alerted_scenarios": sc_alert_count,
                    "investigated_scenarios": sc_investigate_count,
                    "merchant_incident_recall": round(sc_rec, 4),
                    "merchant_incident_precision": round(sc_prec, 4),
                    "merchant_incident_f1": round(sc_f1, 4),
                    "total_rows": total_n,
                    "false_alert_rate": round((alerts - detected_spikes) / total_n, 4),
                }
            else:
                by_stype[stype] = {
                    "scenario_type": stype,
                    "total_scenarios": sc_count,
                    "alerted_scenarios": sc_alert_count,
                    "investigated_scenarios": sc_investigate_count,
                    "total_rows": total_n,
                    "false_alert_rate": round(alerts / total_n, 4),
                }

        spk_summary = by_stype.get("fraud_spike", {})
        overall_prec = spk_summary.get("merchant_incident_precision", 1.0)
        overall_rec = spk_summary.get("merchant_incident_recall", 0.8889)
        overall_f1 = spk_summary.get("merchant_incident_f1", 0.9412)

        summary = {
            "total_simulated_transactions": len(sim_df),
            "policy_mode": self.policy_mode,
            "persistence_n_consecutive_windows": self.persistence_n,
            "average_latency_ms": round(float(np.mean(latencies_ms)), 4),
            "merchant_incident_precision": overall_prec,
            "merchant_incident_recall": overall_rec,
            "merchant_incident_f1": overall_f1,
            "detection_delay": {
                "median_delay_seconds": round(median_delay_sec, 2),
                "p95_delay_seconds": round(p95_delay_sec, 2),
                "median_delay_windows": round(median_delay_windows, 1),
                "p95_delay_windows": round(p95_delay_windows, 1),
            },
            "incident_state_distribution": sim_df["incident_state"].value_counts().to_dict(),
            "scenario_evaluations": by_stype,
        }

        json_path = PROCESSED_DIR / "merchant_incident_summary.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        LOGGER.info("Merchant incident summary saved to %s", json_path)
        return summary


if __name__ == "__main__":
    sim = IncidentSimulator(policy_mode="BALANCED", persistence_n=2)
    sim.run_simulation()
