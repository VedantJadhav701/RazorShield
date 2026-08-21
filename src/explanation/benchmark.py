"""
benchmark.py
------------
RazorShield Zero-Shot Hugging Face SLM Benchmark Suite.

Generates 300+ deterministic evidence examples and gold expectations,
evaluates candidate models across JSON validity, schema validity, numeric grounding,
decision consistency, severity consistency, campaign consistency, signal coverage,
hallucination rate, output length, latency (Load, Avg, P50, P95, P99), and memory usage.

Outputs:
  - data/explanation/evidence_dataset.jsonl
  - data/explanation/benchmark_results.json
  - data/explanation/benchmark_results.csv
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import random
import time
from typing import Any

import numpy as np
import pandas as pd
import torch

from src.explanation.explainer import RazorShieldExplainer
from src.explanation.model_loader import SLMModelLoader
from src.explanation.schemas import ExplanationInput, GoldExpectation

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "explanation"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("slm-benchmark")


def generate_benchmark_dataset(num_examples: int = 300) -> list[dict[str, Any]]:
    """Generates a deterministic dataset of 300+ evidence examples with gold expectations."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataset_path = DATA_DIR / "evidence_dataset.jsonl"

    random.seed(42)
    np.random.seed(42)

    categories = [
        "NORMAL", "INVESTIGATE", "ALERT", "VOLUME_ONLY_SPIKE",
        "AMOUNT_SHIFT", "FRAUD_DURING_CAMPAIGN", "CAMPAIGN_WITHOUT_FRAUD"
    ]

    dataset = []
    per_cat = (num_examples // len(categories)) + 1

    for cat_idx, cat in enumerate(categories):
        for i in range(per_cat):
            m_id = f"M_{100 + ((cat_idx * per_cat + i) % 50)}"

            if cat == "NORMAL":
                inc_state = "NORMAL"
                sev = "LOW"
                score = round(random.uniform(0.01, 0.20), 4)
                spike_p = round(random.uniform(0.01, 0.15), 4)
                fe_ratio = round(random.uniform(0.8, 1.2), 2)
                vel_ratio = round(random.uniform(0.9, 1.2), 2)
                susp_win = 0
                camp = False
                action = "Maintain standard automated processing."
                signals = [{"name": "velocity_ratio", "value": vel_ratio, "direction": "normal"}]

            elif cat == "INVESTIGATE":
                inc_state = "INVESTIGATE"
                sev = "MEDIUM"
                score = round(random.uniform(0.35, 0.55), 4)
                spike_p = round(random.uniform(0.25, 0.45), 4)
                fe_ratio = round(random.uniform(1.8, 2.8), 2)
                vel_ratio = round(random.uniform(1.5, 2.5), 2)
                susp_win = 1
                camp = False
                action = "Monitor merchant stream closely and apply selective verification."
                signals = [
                    {"name": "spike_probability", "value": spike_p, "direction": "elevated"},
                    {"name": "fraud_excess_ratio", "value": fe_ratio, "direction": "elevated"},
                ]

            elif cat == "ALERT":
                inc_state = "ALERT"
                sev = "HIGH"
                score = round(random.uniform(0.68, 0.95), 4)
                spike_p = round(random.uniform(0.50, 0.92), 4)
                fe_ratio = round(random.uniform(3.5, 12.0), 2)
                vel_ratio = round(random.uniform(2.0, 5.0), 2)
                susp_win = random.randint(2, 5)
                camp = False
                action = "Initiate immediate merchant review and enforce step-up authentication."
                signals = [
                    {"name": "spike_probability", "value": spike_p, "direction": "elevated"},
                    {"name": "fraud_excess_ratio", "value": fe_ratio, "direction": "elevated"},
                    {"name": "consecutive_suspicious_windows", "value": susp_win, "direction": "persistent"},
                ]

            elif cat == "VOLUME_ONLY_SPIKE":
                inc_state = "NORMAL"
                sev = "LOW"
                score = round(random.uniform(0.10, 0.25), 4)
                spike_p = round(random.uniform(0.05, 0.20), 4)
                fe_ratio = round(random.uniform(0.8, 1.2), 2)
                vel_ratio = round(random.uniform(3.5, 6.0), 2)
                susp_win = 0
                camp = (i % 2 == 0)
                action = "Normal promotional volume surge. Maintain standard processing."
                signals = [{"name": "velocity_ratio", "value": vel_ratio, "direction": "normal" if camp else "elevated"}]

            elif cat == "AMOUNT_SHIFT":
                inc_state = "NORMAL"
                sev = "LOW"
                score = round(random.uniform(0.12, 0.28), 4)
                spike_p = round(random.uniform(0.05, 0.22), 4)
                fe_ratio = round(random.uniform(0.9, 1.3), 2)
                vel_ratio = round(random.uniform(1.0, 1.5), 2)
                susp_win = 0
                camp = False
                action = "Bulk order shift observed. No fraud excess detected."
                signals = [{"name": "amount_deviation", "value": round(random.uniform(3.0, 7.0), 2), "direction": "elevated"}]

            elif cat == "FRAUD_DURING_CAMPAIGN":
                inc_state = "ALERT"
                sev = "HIGH"
                score = round(random.uniform(0.70, 0.94), 4)
                spike_p = round(random.uniform(0.45, 0.88), 4)
                fe_ratio = round(random.uniform(3.0, 9.0), 2)
                vel_ratio = round(random.uniform(4.0, 6.5), 2)
                susp_win = random.randint(2, 4)
                camp = True
                action = "Flash sale active with elevated fraud excess. Enforce step-up verification."
                signals = [
                    {"name": "fraud_excess_ratio", "value": fe_ratio, "direction": "elevated"},
                    {"name": "velocity_ratio", "value": vel_ratio, "direction": "suppressed"},
                    {"name": "consecutive_suspicious_windows", "value": susp_win, "direction": "persistent"},
                ]

            else:  # CAMPAIGN_WITHOUT_FRAUD
                inc_state = "NORMAL"
                sev = "LOW"
                score = round(random.uniform(0.08, 0.22), 4)
                spike_p = round(random.uniform(0.04, 0.18), 4)
                fe_ratio = round(random.uniform(0.8, 1.1), 2)
                vel_ratio = round(random.uniform(4.0, 6.0), 2)
                susp_win = 0
                camp = True
                action = "Active flash sale with normal fraud excess. Maintain standard processing."
                signals = [{"name": "velocity_ratio", "value": vel_ratio, "direction": "suppressed"}]

            inp = ExplanationInput(
                merchant_id=m_id,
                incident_state=inc_state,
                severity=sev,
                incident_score=score,
                spike_probability=spike_p,
                fraud_excess_ratio=fe_ratio,
                velocity_ratio=vel_ratio,
                suspicious_windows=susp_win,
                total_suspicious_windows=susp_win,
                campaign_active=camp,
                policy_mode="BALANCED",
                signals=signals,
                recommended_action=action,
            )

            gold = GoldExpectation(
                expected_incident_state=inc_state,
                expected_severity=sev,
                required_numeric_values=["fraud_excess_ratio", "velocity_ratio"],
                required_signals=[s["name"] for s in signals],
                campaign_status=camp,
                allowed_actions=["monitor", "review", "verification", "processing", "maintain"],
                forbidden_claims=["$50,000", "IP address", "phishing", "confirmed fraud"],
            )

            dataset.append({
                "example_id": len(dataset) + 1,
                "category": cat,
                "input": inp.model_dump(),
                "gold": gold.model_dump(),
            })

            if len(dataset) >= num_examples:
                break
        if len(dataset) >= num_examples:
            break

    with dataset_path.open("w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")

    LOGGER.info("Generated %d benchmark dataset examples to %s", len(dataset), dataset_path)
    return dataset


def evaluate_candidate_model(
    model_name: str,
    dataset: list[dict[str, Any]],
    device_str: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> dict[str, Any]:
    """Evaluates a candidate SLM across all dataset examples."""
    LOGGER.info("--- Benchmarking Candidate SLM: %s ---", model_name)

    loader = SLMModelLoader(model_name=model_name, device=device_str, max_new_tokens=160, temperature=0.1)

    t_load_start = time.perf_counter()
    load_success = loader.load_model()
    t_load_sec = round(time.perf_counter() - t_load_start, 2)

    if not load_success:
        return {
            "model": model_name,
            "device": device_str,
            "load_success": False,
            "model_load_time_sec": t_load_sec,
            "overall_score": 0.0,
            "note": "Model failed to load",
        }

    explainer = RazorShieldExplainer(model_loader=loader)

    json_valid_count = 0
    schema_valid_count = 0
    numeric_grounded_count = 0
    dec_consistent_count = 0
    sev_consistent_count = 0
    camp_consistent_count = 0
    signal_cov_count = 0
    hallucination_free_count = 0

    word_counts = []
    latencies_ms = []
    model_outputs = []

    for item in dataset:
        inp_data = ExplanationInput(**item["input"])
        gold = GoldExpectation(**item["gold"])

        t_start = time.perf_counter()
        out, val_res = explainer.generate_explanation(inp_data, expectation=gold)
        t_ms = (time.perf_counter() - t_start) * 1000.0
        latencies_ms.append(t_ms)

        word_counts.append(val_res["word_count"])

        if not val_res.get("used_fallback", True):
            json_valid_count += 1
            schema_valid_count += 1

        if val_res["numeric_grounded"]:
            numeric_grounded_count += 1
        if val_res["decision_consistent"]:
            dec_consistent_count += 1
        if val_res["severity_consistent"]:
            sev_consistent_count += 1
        if val_res["campaign_consistent"]:
            camp_consistent_count += 1
        if not val_res["hallucination_detected"]:
            hallucination_free_count += 1

        # Signal coverage check
        signals_in_text = 0
        text_lower = f"{out.summary} {' '.join(out.key_signals)}".lower()
        for s_name in gold.required_signals:
            if s_name.lower().replace("_", " ") in text_lower or s_name.lower() in text_lower:
                signals_in_text += 1
        if not gold.required_signals or signals_in_text >= max(1, len(gold.required_signals) // 2):
            signal_cov_count += 1

        model_outputs.append({
            "example_id": item["example_id"],
            "input": inp_data.model_dump(),
            "output": out.model_dump(),
            "validation": val_res,
        })

    n_total = len(dataset)
    json_validity = round(json_valid_count / n_total, 4)
    schema_validity = round(schema_valid_count / n_total, 4)
    numeric_grounding = round(numeric_grounded_count / n_total, 4)
    decision_consistency = round(dec_consistent_count / n_total, 4)
    severity_consistency = round(sev_consistent_count / n_total, 4)
    campaign_consistency = round(camp_consistent_count / n_total, 4)
    signal_coverage = round(signal_cov_count / n_total, 4)
    hallucination_rate = round(1.0 - (hallucination_free_count / n_total), 4)

    avg_words = round(float(np.mean(word_counts)), 1)
    avg_lat = round(float(np.mean(latencies_ms)), 2)
    p50_lat = round(float(np.median(latencies_ms)), 2)
    p95_lat = round(float(np.percentile(latencies_ms, 95)), 2)
    p99_lat = round(float(np.percentile(latencies_ms, 99)), 2)

    # Formula specified in prompt:
    # quality_score = 0.25*json_validity + 0.20*numeric_grounding + 0.20*decision_consistency + 0.10*severity_consistency + 0.10*campaign_consistency + 0.10*signal_coverage + 0.05*(1 - hallucination_rate)
    quality_score = (
        (0.25 * json_validity)
        + (0.20 * numeric_grounding)
        + (0.20 * decision_consistency)
        + (0.10 * severity_consistency)
        + (0.10 * campaign_consistency)
        + (0.10 * signal_coverage)
        + (0.05 * (1.0 - hallucination_rate))
    )

    mem_usage_mb = round(torch.cuda.memory_allocated() / (1024 * 1024), 2) if torch.cuda.is_available() else 0.0

    res = {
        "model": model_name,
        "load_success": True,
        "device": device_str,
        "model_load_time_sec": t_load_sec,
        "json_validity": json_validity,
        "schema_validity": schema_validity,
        "numeric_grounding": numeric_grounding,
        "decision_consistency": decision_consistency,
        "severity_consistency": severity_consistency,
        "campaign_consistency": campaign_consistency,
        "signal_coverage": signal_coverage,
        "hallucination_rate": hallucination_rate,
        "avg_words": avg_words,
        "avg_latency_ms": avg_lat,
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "p99_latency_ms": p99_lat,
        "memory_usage_mb": mem_usage_mb,
        "quality_score": round(quality_score, 4),
    }

    # Save model outputs log
    out_dir = DATA_DIR / "model_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    sanitized_name = model_name.replace("/", "_").replace("-", "_")
    with (out_dir / f"{sanitized_name}_outputs.json").open("w", encoding="utf-8") as f:
        json.dump(model_outputs, f, indent=2)

    # Clean memory
    del loader
    del explainer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return res


def run_slm_benchmark() -> dict[str, Any]:
    dataset = generate_benchmark_dataset(num_examples=300)

    candidate_models = [
        "Qwen/Qwen2.5-0.5B-Instruct",
        "Qwen/Qwen2.5-1.5B-Instruct",
        "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    ]

    results = []
    for model_name in candidate_models:
        res = evaluate_candidate_model(model_name, dataset)
        results.append(res)

    # Save benchmark_results.json and benchmark_results.csv
    json_path = DATA_DIR / "benchmark_results.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    df_res = pd.DataFrame(results)
    csv_path = DATA_DIR / "benchmark_results.csv"
    df_res.to_csv(csv_path, index=False)

    LOGGER.info("Benchmark complete. Results saved to %s and %s", json_path, csv_path)
    return {"benchmark_results": results}


if __name__ == "__main__":
    run_slm_benchmark()
