"""
audit_dataset_b.py
------------------
Audits Dataset B defensive synthetic scenarios.

Calculates metrics by scenario type, verifies scenario semantic contracts,
flags semantic violations, and produces audit artifacts:
  - data/processed/dataset_b_audit.json
  - data/processed/dataset_b_scenario_summary.parquet
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("audit-dataset-b")


def audit_dataset_b(parquet_path: Path | None = None) -> dict[str, Any]:
    if parquet_path is None:
        parquet_path = PROCESSED_DIR / "dataset_b_scenarios.parquet"

    if not parquet_path.exists():
        raise FileNotFoundError(f"Dataset B file not found: {parquet_path}")

    LOGGER.info("Loading Dataset B from %s ...", parquet_path)
    df = pd.read_parquet(parquet_path)

    # 1. Per-scenario summary table
    scenario_rows = []
    failed_scenarios = []

    for scenario_id, group in df.groupby("scenario_id"):
        s_type = str(group["scenario_type"].iloc[0])
        split = str(group["split"].iloc[0])
        total_rows = len(group)

        base_rows = group[group["spike_window"] == 0]
        spk_rows = group[group["spike_window"] == 1]

        base_fraud = float(base_rows["is_fraud"].mean()) if not base_rows.empty else 0.0
        spk_fraud = float(spk_rows["is_fraud"].mean()) if not spk_rows.empty else 0.0
        fraud_diff = spk_fraud - base_fraud

        base_amt = float(base_rows["amount"].mean()) if not base_rows.empty else 0.0
        spk_amt = float(spk_rows["amount"].mean()) if not spk_rows.empty else base_amt
        amt_shift = spk_amt / max(base_amt, 1e-5)

        base_count = len(base_rows)
        spk_count = len(spk_rows)

        # Estimate minutes
        base_mins = max(1, group[group["spike_window"] == 0]["event_time"].dt.floor("min").nunique())
        spk_mins = max(1, group[group["spike_window"] == 1]["event_time"].dt.floor("min").nunique())

        base_vol_pm = base_count / base_mins
        spk_vol_pm = spk_count / spk_mins if spk_count > 0 else base_vol_pm
        vol_multiplier = spk_vol_pm / max(base_vol_pm, 1e-5)

        max_vel = float(group["velocity_ratio"].max()) if "velocity_ratio" in group.columns else 1.0
        fraud_spike_label = int(group["fraud_spike"].max())

        # Semantic check logic
        sem_pass = True
        sem_notes = []

        if s_type == "normal":
            if fraud_diff >= 0.05:
                sem_pass = False
                sem_notes.append(f"Normal scenario has material fraud rate increase ({fraud_diff:.4f})")
            if fraud_spike_label != 0:
                sem_pass = False
                sem_notes.append("Normal scenario has fraud_spike label == 1")

        elif s_type == "fraud_spike":
            if fraud_diff < 0.03:
                sem_pass = False
                sem_notes.append(f"Fraud spike scenario fraud rate diff too small ({fraud_diff:.4f})")
            if fraud_spike_label != 1:
                sem_pass = False
                sem_notes.append("Fraud spike scenario missing fraud_spike label == 1")

        elif s_type == "volume_only_spike":
            if vol_multiplier < 1.3:
                sem_pass = False
                sem_notes.append(f"Volume spike multiplier too small ({vol_multiplier:.2f}x)")
            if fraud_diff >= 0.05:
                sem_pass = False
                sem_notes.append(f"Volume-only spike has material fraud rate increase ({fraud_diff:.4f})")
            if fraud_spike_label != 0:
                sem_pass = False
                sem_notes.append("Volume-only spike scenario has fraud_spike label == 1")

        elif s_type == "amount_shift":
            if amt_shift < 1.3:
                sem_pass = False
                sem_notes.append(f"Amount shift multiplier too small ({amt_shift:.2f}x)")
            if fraud_diff >= 0.05:
                sem_pass = False
                sem_notes.append(f"Amount shift scenario has material fraud rate increase ({fraud_diff:.4f})")
            if fraud_spike_label != 0:
                sem_pass = False
                sem_notes.append("Amount shift scenario has fraud_spike label == 1")

        summary_entry = {
            "scenario_id": scenario_id,
            "scenario_type": s_type,
            "split": split,
            "rows": total_rows,
            "baseline_fraud_rate": round(base_fraud, 4),
            "spike_fraud_rate": round(spk_fraud, 4),
            "fraud_rate_diff": round(fraud_diff, 4),
            "baseline_amount": round(base_amt, 2),
            "spike_amount": round(spk_amt, 2),
            "amount_shift": round(amt_shift, 2),
            "baseline_vol_pm": round(base_vol_pm, 2),
            "spike_vol_pm": round(spk_vol_pm, 2),
            "volume_multiplier": round(vol_multiplier, 2),
            "max_velocity_ratio": round(max_vel, 2),
            "fraud_spike_label": fraud_spike_label,
            "semantic_pass": sem_pass,
            "semantic_notes": "; ".join(sem_notes) if sem_notes else "OK",
        }

        scenario_rows.append(summary_entry)
        if not sem_pass:
            failed_scenarios.append(summary_entry)

    summary_df = pd.DataFrame(scenario_rows)

    # 2. Aggregation by scenario type
    by_type = {}
    for stype, g in summary_df.groupby("scenario_type"):
        by_type[stype] = {
            "number_of_scenarios": int(len(g)),
            "number_of_transactions": int(g["rows"].sum()),
            "baseline_transaction_volume_pm": round(float(g["baseline_vol_pm"].mean()), 2),
            "spike_transaction_volume_pm": round(float(g["spike_vol_pm"].mean()), 2),
            "volume_multiplier": round(float(g["volume_multiplier"].mean()), 2),
            "baseline_fraud_rate": round(float(g["baseline_fraud_rate"].mean()), 4),
            "spike_fraud_rate": round(float(g["spike_fraud_rate"].mean()), 4),
            "fraud_rate_multiplier_or_deviation": round(float(g["fraud_rate_diff"].mean()), 4),
            "baseline_amount": round(float(g["baseline_amount"].mean()), 2),
            "spike_amount": round(float(g["spike_amount"].mean()), 2),
            "amount_shift": round(float(g["amount_shift"].mean()), 2),
            "maximum_velocity_ratio": round(float(g["max_velocity_ratio"].max()), 2),
            "semantic_pass_count": int(g["semantic_pass"].sum()),
            "semantic_fail_count": int((~g["semantic_pass"]).sum()),
        }

    # 3. Save outputs
    summary_parquet_path = PROCESSED_DIR / "dataset_b_scenario_summary.parquet"
    summary_df.to_parquet(summary_parquet_path, index=False)
    LOGGER.info("Dataset B scenario summary written to %s", summary_parquet_path)

    audit_json = {
        "dataset": "Dataset B (Defensive Synthetic Scenarios)",
        "total_scenarios": int(len(summary_df)),
        "total_transactions": int(len(df)),
        "by_scenario_type": by_type,
        "overall_semantic_pass_count": int(summary_df["semantic_pass"].sum()),
        "overall_semantic_fail_count": int((~summary_df["semantic_pass"]).sum()),
        "failed_scenarios": failed_scenarios,
    }

    json_path = PROCESSED_DIR / "dataset_b_audit.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(audit_json, f, indent=2)

    LOGGER.info("Dataset B audit JSON written to %s", json_path)
    return audit_json


if __name__ == "__main__":
    audit_dataset_b()
