"""
data.py
-------
End-to-end data acquisition + dataset construction for RazorShield.

Creates:
    data/
      raw/
        ieee_cis/
      processed/
        dataset_a_model.parquet
        dataset_b_scenarios.parquet
        scenario_specs.json
        metadata.json

Dataset A:
    Public IEEE-CIS transaction data, normalized into a leakage-aware
    transaction-level model dataset with a chronological train/val/test split.

Dataset B:
    Defensive synthetic merchant scenarios. NVIDIA's hosted OpenAI-compatible
    API generates ABSTRACT scenario specifications in parallel; Python/Numpy
    generates the actual numeric transaction rows deterministically.

Important:
    We deliberately do NOT ask the LLM to generate millions of transaction rows.
    The LLM proposes bounded scenario parameters; the deterministic generator
    creates the rows. This is more reproducible, cheaper, and easier to audit.

Environment:
    KAGGLE_API_TOKEN / Kaggle credentials for IEEE-CIS download
    NVIDIA_API_KEY for hosted NVIDIA inference

Typical usage:
    python data.py --download-public
    python data.py --build-model
    python data.py --generate-scenarios
    python data.py --all

Useful overrides:
    --workers 4
    --scenarios 60
    --batch-size 5
    --rows-per-minute-cap 50
    --seed 42
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "ieee_cis"
PROCESSED_DIR = DATA_DIR / "processed"

KAGGLE_COMPETITION = "ieee-fraud-detection"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

DEFAULT_NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL",
    "openai/gpt-oss-20b",
)

DEFAULT_WORKERS = int(os.getenv("NVIDIA_WORKERS", "4"))
DEFAULT_SCENARIOS = int(os.getenv("SYNTHETIC_SCENARIOS", "60"))
DEFAULT_BATCH_SIZE = int(os.getenv("NVIDIA_BATCH_SIZE", "5"))
DEFAULT_SEED = int(os.getenv("DATA_SEED", "42"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("razorshield-data")


def load_environment() -> None:
    """Load environment variables from .env or api_keys.txt if present."""
    env_file = ROOT / ".env"
    if env_file.exists():
        try:
            import dotenv
            dotenv.load_dotenv(env_file)
        except ImportError:
            pass

    api_keys_file = ROOT / "api_keys.txt"
    if api_keys_file.exists():
        try:
            text = api_keys_file.read_text(encoding="utf-8")
            if not os.getenv("KAGGLE_API_TOKEN"):
                m = re.search(r"kaggle api token:\s*(\S+)", text, re.IGNORECASE)
                if m:
                    os.environ["KAGGLE_API_TOKEN"] = m.group(1).strip()
            if not os.getenv("NVIDIA_API_KEY"):
                m = re.search(r"api_key\s*=\s*[\"'](nvapi-\S+)[\"']", text)
                if not m:
                    m = re.search(r"nvidia api token:\s*(\S+)", text, re.IGNORECASE)
                if m:
                    os.environ["NVIDIA_API_KEY"] = m.group(1).strip()
        except Exception as exc:
            LOGGER.warning("Could not parse api_keys.txt: %s", exc)



# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ScenarioSpec:
    scenario_id: str
    scenario_type: str
    duration_minutes: int
    spike_start_minute: int
    spike_duration_minutes: int
    baseline_txn_per_minute: float
    spike_txn_multiplier: float
    baseline_fraud_rate: float
    spike_fraud_rate: float
    amount_mean: float
    amount_std: float
    customer_count: int
    device_count: int
    new_device_rate: float
    seed: int


ALLOWED_SCENARIOS = {
    "normal",
    "fraud_spike",
    "volume_only_spike",
    "amount_shift",
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def stable_id(value: Any, prefix: str = "") -> str:
    digest = hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}{digest}"


def clamp(value: Any, low: float, high: float, default: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return float(np.clip(value, low, high))


def clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        value = int(float(value))
    except (TypeError, ValueError):
        return default
    return int(np.clip(value, low, high))


def parse_json_from_text(text: str) -> Any:
    """
    Robustly parse JSON from an LLM response that may contain:
      - plain JSON
      - ```json ... ```
      - explanatory text surrounding JSON
    """
    text = (text or "").strip()

    # Remove markdown fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first JSON array/object.
    candidates = []
    first_array = text.find("[")
    last_array = text.rfind("]")
    if first_array >= 0 and last_array > first_array:
        candidates.append(text[first_array:last_array + 1])

    first_object = text.find("{")
    last_object = text.rfind("}")
    if first_object >= 0 and last_object > first_object:
        candidates.append(text[first_object:last_object + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError("Could not parse JSON from NVIDIA response.")


# ---------------------------------------------------------------------------
# Public data acquisition
# ---------------------------------------------------------------------------

def download_ieee_cis(force: bool = False) -> tuple[Path, Path]:
    """
    Download only the two training files needed from IEEE-CIS.

    Kaggle competition rules must be accepted on the competition page before
    the API can download the data.
    """
    ensure_dirs()

    tx_path = RAW_DIR / "train_transaction.csv"
    id_path = RAW_DIR / "train_identity.csv"

    if tx_path.exists() and id_path.exists() and not force:
        LOGGER.info("IEEE-CIS files already exist. Skipping download.")
        return tx_path, id_path

    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError(
            "Install kagglehub first: pip install kagglehub"
        ) from exc

    try:
        LOGGER.info("Downloading IEEE-CIS train_transaction.csv ...")
        downloaded_tx = kagglehub.competition_download(
            KAGGLE_COMPETITION,
            path="train_transaction.csv",
            output_dir=str(RAW_DIR),
            force_download=force,
        )

        LOGGER.info("Downloading IEEE-CIS train_identity.csv ...")
        downloaded_id = kagglehub.competition_download(
            KAGGLE_COMPETITION,
            path="train_identity.csv",
            output_dir=str(RAW_DIR),
            force_download=force,
        )
    except Exception as exc:
        err_msg = str(exc)
        if "403" in err_msg or "permission" in err_msg.lower() or "rules" in err_msg.lower():
            raise RuntimeError(
                "\n============================================================"
                "\nKAGGLE ACCESS DENIED / COMPETITION RULES NOT ACCEPTED"
                "\n============================================================"
                "\nTo download the IEEE-CIS Fraud Detection dataset:"
                "\n1. Ensure KAGGLE_API_TOKEN environment variable is set."
                "\n2. Visit: https://www.kaggle.com/competitions/ieee-fraud-detection/rules"
                "\n   and click 'I Understand and Accept' on Kaggle."
                "\n3. Re-run the command once competition rules are accepted."
                "\n============================================================"
            ) from exc
        elif not os.getenv("KAGGLE_API_TOKEN") and not (Path.home() / ".kaggle" / "kaggle.json").exists():
            raise RuntimeError(
                "\n============================================================"
                "\nMISSING KAGGLE CREDENTIALS"
                "\n============================================================"
                "\nKAGGLE_API_TOKEN or Kaggle credentials (~/.kaggle/kaggle.json) not found."
                "\nPlease set the KAGGLE_API_TOKEN environment variable."
                "\n============================================================"
            ) from exc
        raise

    tx_path = Path(downloaded_tx)
    id_path = Path(downloaded_id)

    LOGGER.info("Transaction file: %s", tx_path)
    LOGGER.info("Identity file: %s", id_path)

    return tx_path, id_path


# ---------------------------------------------------------------------------
# Dataset A — Model dataset
# ---------------------------------------------------------------------------

TRANSACTION_COLS = [
    "TransactionID",
    "TransactionDT",
    "TransactionAmt",
    "ProductCD",
    "card1",
    "card2",
    "card3",
    "card4",
    "card5",
    "card6",
    "addr1",
    "addr2",
    "P_emaildomain",
    "R_emaildomain",
    "isFraud",
]

IDENTITY_COLS = [
    "TransactionID",
    "DeviceType",
    "DeviceInfo",
]


def load_ieee_cis(
    transaction_path: Path,
    identity_path: Path,
) -> pd.DataFrame:
    LOGGER.info("Reading IEEE-CIS transaction data ...")

    tx_comp = "zip" if zipfile.is_zipfile(transaction_path) else None

    tx = pd.read_csv(
        transaction_path,
        usecols=lambda c: c in TRANSACTION_COLS,
        compression=tx_comp,
        low_memory=False,
    )

    LOGGER.info(
        "Transaction rows=%s columns=%s",
        f"{len(tx):,}",
        len(tx.columns),
    )

    if identity_path.exists():
        LOGGER.info("Reading IEEE-CIS identity data ...")
        id_comp = "zip" if zipfile.is_zipfile(identity_path) else None
        identity = pd.read_csv(
            identity_path,
            usecols=lambda c: c in IDENTITY_COLS,
            compression=id_comp,
            low_memory=False,
        )
        df = tx.merge(
            identity,
            on="TransactionID",
            how="left",
        )
    else:
        df = tx.copy()
        df["DeviceType"] = "unknown"
        df["DeviceInfo"] = "unknown"

    return df


def build_model_dataset(
    transaction_path: Path,
    identity_path: Path,
    seed: int = DEFAULT_SEED,
) -> Path:
    """
    Build Dataset A.

    The public dataset does not expose a merchant_id. Therefore Dataset A
    is explicitly a transaction-level fraud model dataset. Merchant-level
    temporal behavior is covered by Dataset B.

    We create privacy-preserving proxy identifiers only for modeling:
        customer_proxy_id
        device_proxy_id

    No raw IP addresses, names, emails, or other direct identifiers are added.
    """
    df = load_ieee_cis(transaction_path, identity_path)

    # Relative TransactionDT is converted to a synthetic reference timestamp.
    # It is not claimed to be the original real-world timestamp.
    origin = pd.Timestamp("2017-12-01", tz="UTC")
    df["event_time"] = origin + pd.to_timedelta(
        pd.to_numeric(df["TransactionDT"], errors="coerce"),
        unit="s",
    )

    df["amount"] = pd.to_numeric(
        df["TransactionAmt"],
        errors="coerce",
    ).fillna(0.0)

    df["amount_log1p"] = np.log1p(np.clip(df["amount"], 0, None))

    # Privacy-preserving deterministic proxies.
    customer_key = (
        df["card1"].astype("string").fillna("NA")
        + "|"
        + df["addr1"].astype("string").fillna("NA")
        + "|"
        + df["P_emaildomain"].astype("string").fillna("NA")
    )

    device_key = (
        df["DeviceType"].astype("string").fillna("NA")
        + "|"
        + df["DeviceInfo"].astype("string").fillna("NA")
    )

    df["customer_proxy_id"] = (
        pd.util.hash_pandas_object(customer_key, index=False)
        .astype("uint64")
        .astype("string")
    )

    df["device_proxy_id"] = (
        pd.util.hash_pandas_object(device_key, index=False)
        .astype("uint64")
        .astype("string")
    )

    # Time features.
    df["hour"] = df["event_time"].dt.hour.astype("int8")
    df["day_of_week"] = df["event_time"].dt.dayofweek.astype("int8")
    df["is_weekend"] = (df["day_of_week"] >= 5).astype("int8")

    # Simple missingness indicators are useful for IEEE-CIS.
    df["identity_available"] = (
        df["DeviceInfo"].notna() | df["DeviceType"].notna()
    ).astype("int8")

    # Remove obvious raw columns that are not needed in the canonical dataset.
    keep = [
        "TransactionID",
        "event_time",
        "amount",
        "amount_log1p",
        "ProductCD",
        "card1",
        "card2",
        "card3",
        "card4",
        "card5",
        "card6",
        "addr1",
        "addr2",
        "P_emaildomain",
        "R_emaildomain",
        "DeviceType",
        "DeviceInfo",
        "customer_proxy_id",
        "device_proxy_id",
        "hour",
        "day_of_week",
        "is_weekend",
        "identity_available",
        "isFraud",
    ]

    df = df[keep].copy()
    df = df.sort_values("event_time").reset_index(drop=True)

    # Chronological split: no random mixing of future observations into train.
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    df["split"] = "test"
    df.loc[:train_end - 1, "split"] = "train"
    df.loc[train_end:val_end - 1, "split"] = "validation"

    df["isFraud"] = pd.to_numeric(
        df["isFraud"],
        errors="coerce",
    ).fillna(0).astype("int8")

    output = PROCESSED_DIR / "dataset_a_model.parquet"
    df.to_parquet(output, index=False)

    LOGGER.info(
        "Dataset A written: %s | rows=%s | fraud=%s",
        output,
        f"{len(df):,}",
        f"{df['isFraud'].sum():,}",
    )

    return output


# ---------------------------------------------------------------------------
# NVIDIA synthetic scenario specification generation
# ---------------------------------------------------------------------------

def nvidia_client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "Install the OpenAI client: pip install openai"
        ) from exc

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY is not set. Create an NVIDIA Build API key "
            "and export it before running --generate-scenarios."
        )

    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=api_key,
        timeout=120.0,
        max_retries=0,
    )


def scenario_prompt(count: int, seed: int) -> str:
    return f"""
You are generating DEFENSIVE synthetic data specifications for a fintech
fraud-spike detection benchmark.

This is strictly defensive. Do not provide attack instructions, exploit
instructions, evasion strategies, credential abuse, or operational fraud
guidance. Only generate abstract statistical parameters for simulation.

Return EXACTLY a JSON array with {count} objects and no markdown.

Allowed scenario_type:
- normal
- fraud_spike
- volume_only_spike
- amount_shift

Required fields for every object:
scenario_type
duration_minutes
spike_start_minute
spike_duration_minutes
baseline_txn_per_minute
spike_txn_multiplier
baseline_fraud_rate
spike_fraud_rate
amount_mean
amount_std
customer_count
device_count
new_device_rate
seed

Constraints:
duration_minutes: 120 to 360
spike_start_minute: 30 to duration_minutes-60
spike_duration_minutes: 15 to 60
baseline_txn_per_minute: 3 to 30
spike_txn_multiplier: 1.0 to 10.0
baseline_fraud_rate: 0.002 to 0.03
spike_fraud_rate: 0.002 to 0.30
amount_mean: 100 to 5000
amount_std: 20 to 2500
customer_count: 100 to 5000
device_count: 50 to 3000
new_device_rate: 0.0 to 0.25

Scenario semantics:
- normal: no material fraud-rate increase
- fraud_spike: fraud rate increases during the spike window
- volume_only_spike: transaction volume increases but fraud rate remains
  approximately at baseline; this is a HARD NEGATIVE
- amount_shift: amount distribution changes without requiring a fraud-rate
  increase; this is another HARD NEGATIVE

Keep values statistically plausible. Use seed values derived from {seed}.
"""


def normalize_spec(raw: dict[str, Any], index: int, base_seed: int) -> ScenarioSpec:
    scenario_type = str(raw.get("scenario_type", "normal")).strip().lower()
    if scenario_type not in ALLOWED_SCENARIOS:
        scenario_type = "normal"

    duration = clamp_int(
        raw.get("duration_minutes"),
        120,
        360,
        240,
    )

    spike_start = clamp_int(
        raw.get("spike_start_minute"),
        30,
        max(31, duration - 60),
        90,
    )

    spike_duration = clamp_int(
        raw.get("spike_duration_minutes"),
        15,
        min(60, duration - spike_start),
        30,
    )

    baseline_fraud = clamp(
        raw.get("baseline_fraud_rate"),
        0.002,
        0.03,
        0.01,
    )

    spike_fraud = clamp(
        raw.get("spike_fraud_rate"),
        0.002,
        0.30,
        0.08 if scenario_type == "fraud_spike" else baseline_fraud,
    )

    if scenario_type != "fraud_spike":
        spike_fraud = baseline_fraud

    multiplier = clamp(
        raw.get("spike_txn_multiplier"),
        1.0,
        10.0,
        1.0,
    )

    if scenario_type == "normal":
        multiplier = 1.0
    elif scenario_type == "volume_only_spike":
        multiplier = max(multiplier, 2.0)

    return ScenarioSpec(
        scenario_id=f"S{index:05d}",
        scenario_type=scenario_type,
        duration_minutes=duration,
        spike_start_minute=spike_start,
        spike_duration_minutes=spike_duration,
        baseline_txn_per_minute=clamp(
            raw.get("baseline_txn_per_minute"),
            3,
            30,
            10,
        ),
        spike_txn_multiplier=multiplier,
        baseline_fraud_rate=baseline_fraud,
        spike_fraud_rate=spike_fraud,
        amount_mean=clamp(
            raw.get("amount_mean"),
            100,
            5000,
            1000,
        ),
        amount_std=clamp(
            raw.get("amount_std"),
            20,
            2500,
            500,
        ),
        customer_count=clamp_int(
            raw.get("customer_count"),
            100,
            5000,
            1000,
        ),
        device_count=clamp_int(
            raw.get("device_count"),
            50,
            3000,
            500,
        ),
        new_device_rate=clamp(
            raw.get("new_device_rate"),
            0,
            0.25,
            0.05,
        ),
        seed=clamp_int(
            raw.get("seed"),
            1,
            2_000_000_000,
            base_seed + index,
        ),
    )


def request_scenario_batch(
    client,
    batch_count: int,
    batch_index: int,
    base_seed: int,
    retries: int = 3,
) -> list[dict[str, Any]]:
    prompt = scenario_prompt(
        count=batch_count,
        seed=base_seed + batch_index * 10_000,
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=DEFAULT_NVIDIA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict JSON generator for defensive "
                            "financial ML simulation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                top_p=0.8,
                max_tokens=2500,
                stream=False,
            )

            content = response.choices[0].message.content
            parsed = parse_json_from_text(content)

            if isinstance(parsed, dict):
                parsed = [parsed]

            if not isinstance(parsed, list):
                raise ValueError("NVIDIA response is not a JSON list.")

            return parsed

        except Exception as exc:
            wait = 2 ** attempt
            LOGGER.warning(
                "NVIDIA batch %s failed (attempt %s/%s): %s; retrying in %ss",
                batch_index,
                attempt + 1,
                retries,
                exc,
                wait,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"NVIDIA batch {batch_index} failed after {retries} attempts."
    )


def generate_scenario_specs(
    count: int = DEFAULT_SCENARIOS,
    workers: int = DEFAULT_WORKERS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed: int = DEFAULT_SEED,
    offline: bool = False,
) -> list[ScenarioSpec]:
    """
    Generate bounded scenario specifications.

    workers controls concurrent NVIDIA requests, NOT raw transaction-row
    generation. Raw rows are generated locally and deterministically.
    """
    if offline:
        LOGGER.warning(
            "OFFLINE mode: using deterministic fallback specifications; "
            "NVIDIA API is not called."
        )
        return make_offline_specs(count, seed)

    client = nvidia_client()

    batches = []
    remaining = count
    batch_index = 0

    while remaining > 0:
        n = min(batch_size, remaining)
        batches.append((batch_index, n))
        remaining -= n
        batch_index += 1

    LOGGER.info(
        "Generating %s scenario specs using NVIDIA model=%s workers=%s",
        count,
        DEFAULT_NVIDIA_MODEL,
        workers,
    )

    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(
                request_scenario_batch,
                client,
                batch_count,
                batch_idx,
                seed,
            ): batch_idx
            for batch_idx, batch_count in batches
        }

        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                batch = future.result()
                results.extend(batch)
                LOGGER.info(
                    "Completed NVIDIA batch %s: %s specs",
                    batch_idx,
                    len(batch),
                )
            except Exception as exc:
                LOGGER.error(
                    "NVIDIA batch %s failed permanently: %s",
                    batch_idx,
                    exc,
                )

    if not results:
        raise RuntimeError(
            "No NVIDIA scenario specifications were generated."
        )

    specs = []
    for i, raw in enumerate(results[:count]):
        specs.append(normalize_spec(raw, i, seed))

    # Ensure all four classes exist when enough scenarios are requested.
    required = ["normal", "fraud_spike", "volume_only_spike", "amount_shift"]
    for i, required_type in enumerate(required):
        if i < len(specs):
            specs[i].scenario_type = required_type
            if required_type == "fraud_spike":
                specs[i].spike_fraud_rate = max(
                    specs[i].spike_fraud_rate,
                    0.08,
                )
            elif required_type != "fraud_spike":
                specs[i].spike_fraud_rate = specs[i].baseline_fraud_rate
            if required_type == "volume_only_spike":
                specs[i].spike_txn_multiplier = max(
                    specs[i].spike_txn_multiplier,
                    2.0,
                )
            if required_type == "normal":
                specs[i].spike_txn_multiplier = 1.0

    return specs


def make_offline_specs(count: int, seed: int) -> list[ScenarioSpec]:
    """
    Local deterministic fallback for development/testing.
    It is not the final NVIDIA-generated dataset.
    """
    rng = np.random.default_rng(seed)
    types = ["normal", "fraud_spike", "volume_only_spike", "amount_shift"]

    specs = []
    for i in range(count):
        scenario_type = types[i % len(types)]
        duration = int(rng.integers(180, 301))
        start = int(rng.integers(45, max(46, duration - 45)))
        duration_spike = int(rng.integers(20, 51))
        baseline = float(rng.uniform(5, 20))
        base_fraud = float(rng.uniform(0.005, 0.02))

        if scenario_type == "fraud_spike":
            spike_fraud = float(rng.uniform(0.08, 0.20))
            multiplier = float(rng.uniform(1.5, 4.0))
        elif scenario_type == "volume_only_spike":
            spike_fraud = base_fraud
            multiplier = float(rng.uniform(2.5, 7.0))
        elif scenario_type == "amount_shift":
            spike_fraud = base_fraud
            multiplier = 1.0
        else:
            spike_fraud = base_fraud
            multiplier = 1.0

        specs.append(
            ScenarioSpec(
                scenario_id=f"S{i:05d}",
                scenario_type=scenario_type,
                duration_minutes=duration,
                spike_start_minute=start,
                spike_duration_minutes=min(
                    duration_spike,
                    duration - start,
                ),
                baseline_txn_per_minute=baseline,
                spike_txn_multiplier=multiplier,
                baseline_fraud_rate=base_fraud,
                spike_fraud_rate=spike_fraud,
                amount_mean=float(rng.uniform(300, 2500)),
                amount_std=float(rng.uniform(100, 1000)),
                customer_count=int(rng.integers(500, 3000)),
                device_count=int(rng.integers(200, 1500)),
                new_device_rate=float(rng.uniform(0.01, 0.15)),
                seed=seed + i,
            )
        )

    return specs


# ---------------------------------------------------------------------------
# Deterministic synthetic transaction generation
# ---------------------------------------------------------------------------

def generate_scenario_rows(spec: ScenarioSpec) -> pd.DataFrame:
    rng = np.random.default_rng(spec.seed)

    merchant_id = f"M_{spec.scenario_id}"
    start_time = pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(
        days=int(spec.scenario_id[1:]) % 180
    )

    rows = []

    for minute in range(spec.duration_minutes):
        in_spike = (
            spec.spike_start_minute
            <= minute
            < spec.spike_start_minute + spec.spike_duration_minutes
        )

        # Volume behavior.
        multiplier = (
            spec.spike_txn_multiplier
            if in_spike
            else 1.0
        )

        # Amount behavior.
        amount_mean = spec.amount_mean
        amount_std = spec.amount_std

        if spec.scenario_type == "amount_shift" and in_spike:
            amount_mean *= 2.5
            amount_std *= 1.8

        expected = spec.baseline_txn_per_minute * multiplier
        n_transactions = int(
            np.clip(
                rng.poisson(expected),
                1,
                50,
            )
        )

        # Fraud behavior.
        fraud_rate = (
            spec.spike_fraud_rate
            if (
                spec.scenario_type == "fraud_spike"
                and in_spike
            )
            else spec.baseline_fraud_rate
        )

        for _ in range(n_transactions):
            customer_idx = int(
                rng.integers(0, spec.customer_count)
            )
            device_idx = int(
                rng.integers(0, spec.device_count)
            )

            amount = float(
                max(
                    1.0,
                    rng.normal(
                        amount_mean,
                        max(1.0, amount_std),
                    ),
                )
            )

            is_fraud = int(rng.random() < fraud_rate)

            # New-device signal is probabilistic and becomes more common
            # during suspicious periods, but remains abstract/synthetic.
            new_device_prob = spec.new_device_rate
            if spec.scenario_type == "fraud_spike" and in_spike:
                new_device_prob = min(
                    0.5,
                    new_device_prob * 2.5,
                )

            is_new_device = int(
                rng.random() < new_device_prob
            )

            event_time = (
                start_time
                + pd.Timedelta(minutes=minute)
                + pd.Timedelta(
                    seconds=int(rng.integers(0, 60))
                )
            )

            rows.append(
                {
                    "scenario_id": spec.scenario_id,
                    "scenario_type": spec.scenario_type,
                    "merchant_id": merchant_id,
                    "event_time": event_time,
                    "customer_id": f"C_{customer_idx:05d}",
                    "device_id": f"D_{device_idx:05d}",
                    "amount": round(amount, 2),
                    "payment_method": str(
                        rng.choice(
                            ["card", "upi", "wallet", "netbanking"]
                        )
                    ),
                    "transaction_type": "purchase",
                    "is_new_device": is_new_device,
                    "is_fraud": is_fraud,
                    "spike_window": int(in_spike),
                    "fraud_spike": int(
                        spec.scenario_type == "fraud_spike"
                        and in_spike
                    ),
                }
            )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.sort_values("event_time").reset_index(drop=True)

    # Minute bucket.
    df["minute_bucket"] = df["event_time"].dt.floor("min")

    # Merchant temporal features.
    per_minute = (
        df.groupby("minute_bucket", as_index=False)
        .agg(
            minute_txn_count=("transaction_id_temp", "count")
            if "transaction_id_temp" in df.columns
            else ("amount", "size"),
            minute_fraud_count=("is_fraud", "sum"),
            minute_amount_sum=("amount", "sum"),
        )
    )

    per_minute["rolling_txn_15m"] = (
        per_minute["minute_txn_count"]
        .rolling(15, min_periods=1)
        .sum()
    )

    per_minute["rolling_fraud_15m"] = (
        per_minute["minute_fraud_count"]
        .rolling(15, min_periods=1)
        .sum()
    )

    per_minute["rolling_fraud_rate_15m"] = (
        per_minute["rolling_fraud_15m"]
        / per_minute["rolling_txn_15m"].clip(lower=1)
    )

    # Baseline from the first 30 minutes. This avoids using future spike data
    # to define the baseline.
    baseline_window = per_minute.iloc[
        : min(30, len(per_minute))
    ]

    baseline_txn_15m = float(
        baseline_window["minute_txn_count"].mean() * 15
    )

    baseline_fraud_rate = float(
        baseline_window["minute_fraud_count"].sum()
        / max(1, baseline_window["minute_txn_count"].sum())
    )

    per_minute["baseline_txn_15m"] = max(
        1.0,
        baseline_txn_15m,
    )

    per_minute["baseline_fraud_rate"] = baseline_fraud_rate

    per_minute["velocity_ratio"] = (
        per_minute["rolling_txn_15m"]
        / per_minute["baseline_txn_15m"]
    )

    per_minute["fraud_rate_deviation"] = (
        per_minute["rolling_fraud_rate_15m"]
        - per_minute["baseline_fraud_rate"]
    )

    # Amount anomaly relative to baseline.
    baseline_amount = float(
        baseline_window["minute_amount_sum"].mean()
        / baseline_window["minute_txn_count"].clip(lower=1).mean()
    )

    per_minute["baseline_amount"] = max(
        1.0,
        baseline_amount,
    )

    # Map minute-level features back to transactions.
    df = df.merge(
        per_minute[
            [
                "minute_bucket",
                "rolling_txn_15m",
                "rolling_fraud_rate_15m",
                "baseline_txn_15m",
                "baseline_fraud_rate",
                "velocity_ratio",
                "fraud_rate_deviation",
                "baseline_amount",
            ]
        ],
        on="minute_bucket",
        how="left",
    )

    df["amount_deviation"] = (
        df["amount"] / df["baseline_amount"].clip(lower=1)
    )

    df["merchant_txn_count_15m"] = (
        df["rolling_txn_15m"].round().astype("int32")
    )

    # Stable transaction ID.
    df.insert(
        0,
        "transaction_id",
        [
            f"T_{spec.scenario_id}_{i:07d}"
            for i in range(len(df))
        ],
    )

    # Remove helper column.
    df = df.drop(columns=["minute_bucket"])

    return df


def generate_synthetic_dataset(
    specs: list[ScenarioSpec],
) -> Path:
    frames = []

    for i, spec in enumerate(specs, start=1):
        frame = generate_scenario_rows(spec)
        frames.append(frame)

        if i % 10 == 0 or i == len(specs):
            LOGGER.info(
                "Generated %s/%s synthetic scenarios",
                i,
                len(specs),
            )

    df = pd.concat(frames, ignore_index=True)

    # Scenario-level chronological split.
    scenario_ids = sorted(df["scenario_id"].unique())
    n = len(scenario_ids)
    train_ids = set(scenario_ids[: int(n * 0.70)])
    val_ids = set(
        scenario_ids[
            int(n * 0.70): int(n * 0.85)
        ]
    )

    df["split"] = np.where(
        df["scenario_id"].isin(train_ids),
        "train",
        np.where(
            df["scenario_id"].isin(val_ids),
            "validation",
            "test",
        ),
    )

    output = PROCESSED_DIR / "dataset_b_scenarios.parquet"
    df.to_parquet(output, index=False)

    LOGGER.info(
        "Dataset B written: %s | rows=%s | scenarios=%s",
        output,
        f"{len(df):,}",
        df["scenario_id"].nunique(),
    )

    return output


def save_specs(specs: list[ScenarioSpec]) -> Path:
    path = PROCESSED_DIR / "scenario_specs.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            [asdict(s) for s in specs],
            f,
            indent=2,
        )

    return path


def write_metadata(
    model_path: Path | None,
    scenario_path: Path | None,
    specs_path: Path | None,
) -> Path:
    metadata = {
        "project": "RazorShield",
        "purpose": "Defensive fraud-spike detection",
        "dataset_a": {
            "name": "IEEE-CIS Fraud Detection",
            "source": (
                "https://www.kaggle.com/competitions/"
                "ieee-fraud-detection"
            ),
            "local_path": str(model_path) if model_path else None,
            "split": "chronological 70/15/15",
        },
        "dataset_b": {
            "name": "RazorShield Defensive Synthetic Scenarios",
            "local_path": str(scenario_path) if scenario_path else None,
            "split": "scenario-level 70/15/15",
            "scenario_types": sorted(ALLOWED_SCENARIOS),
            "nvidia_model": DEFAULT_NVIDIA_MODEL,
            "nvidia_endpoint": NVIDIA_BASE_URL,
            "scenario_specs": (
                str(specs_path) if specs_path else None
            ),
        },
        "principles": [
            "No offensive fraud instructions are generated.",
            "LLM generates bounded scenario parameters, not raw transaction rows.",
            "Numeric synthetic rows are generated deterministically with NumPy.",
            "Future observations are not used for Dataset A chronological split.",
            "Dataset B is split by scenario, not by random transaction rows.",
        ],
    }

    path = PROCESSED_DIR / "metadata.json"

    with path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return path


def generate_validation_report(
    model_path: Path | None = None,
    scenario_path: Path | None = None,
) -> Path:
    """Generate validation_report.json summarizing dataset metrics and data quality checks."""
    report: dict[str, Any] = {
        "dataset_a": None,
        "dataset_b": None,
        "validation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if model_path is None:
        model_path = PROCESSED_DIR / "dataset_a_model.parquet"
    if scenario_path is None:
        scenario_path = PROCESSED_DIR / "dataset_b_scenarios.parquet"

    if model_path.exists():
        df_a = pd.read_parquet(model_path)
        missing_pct = (df_a.isna().mean() * 100).round(2).to_dict()
        split_counts = df_a["split"].value_counts().to_dict()
        fraud_per_split = {
            str(k): int(v)
            for k, v in df_a.groupby("split")["isFraud"].sum().to_dict().items()
        }
        fraud_pct_per_split = {
            str(k): round(float(v * 100), 3)
            for k, v in df_a.groupby("split")["isFraud"].mean().to_dict().items()
        }

        train_df = df_a[df_a["split"] == "train"]
        val_df = df_a[df_a["split"] == "validation"]
        test_df = df_a[df_a["split"] == "test"]

        broken_split = False
        if not train_df.empty and not val_df.empty:
            if train_df["event_time"].max() > val_df["event_time"].min():
                broken_split = True
        if not val_df.empty and not test_df.empty:
            if val_df["event_time"].max() > test_df["event_time"].min():
                broken_split = True

        dup_ids = int(df_a["TransactionID"].duplicated().sum())
        invalid_targets = int((~df_a["isFraud"].isin([0, 1])).sum())
        negative_amounts = int((df_a["amount"] < 0).sum())
        missing_times = int(df_a["event_time"].isna().sum())
        num_cols = df_a.select_dtypes(include=[np.number]).columns
        inf_values = (
            int(np.isinf(df_a[num_cols]).sum().sum())
            if len(num_cols) > 0
            else 0
        )

        report["dataset_a"] = {
            "total_rows": len(df_a),
            "total_columns": len(df_a.columns),
            "fraud_count": int(df_a["isFraud"].sum()),
            "fraud_percentage": round(float(df_a["isFraud"].mean() * 100), 3),
            "missing_percentage_per_column": missing_pct,
            "duplicate_transaction_ids": dup_ids,
            "min_event_time": str(df_a["event_time"].min()),
            "max_event_time": str(df_a["event_time"].max()),
            "train_rows": int(split_counts.get("train", 0)),
            "validation_rows": int(split_counts.get("validation", 0)),
            "test_rows": int(split_counts.get("test", 0)),
            "fraud_count_per_split": fraud_per_split,
            "fraud_percentage_per_split": fraud_pct_per_split,
            "checks": {
                "duplicate_ids": dup_ids == 0,
                "valid_targets": invalid_targets == 0,
                "no_negative_amounts": negative_amounts == 0,
                "no_missing_event_time": missing_times == 0,
                "valid_chronological_split": not broken_split,
                "no_infinite_values": inf_values == 0,
            },
        }

    if scenario_path.exists():
        df_b = pd.read_parquet(scenario_path)
        scenario_summaries = []
        for scenario_id, group in df_b.groupby("scenario_id"):
            s_type = group["scenario_type"].iloc[0]
            baseline_rows = group[group["spike_window"] == 0]
            spike_rows = group[group["spike_window"] == 1]

            base_fraud = (
                float(baseline_rows["is_fraud"].mean())
                if not baseline_rows.empty
                else 0.0
            )
            spk_fraud = (
                float(spike_rows["is_fraud"].mean())
                if not spike_rows.empty
                else 0.0
            )

            base_vol = len(baseline_rows)
            spk_vol = len(spike_rows)
            max_vel = (
                float(group["velocity_ratio"].max())
                if "velocity_ratio" in group.columns
                else 1.0
            )
            label = int(group["fraud_spike"].max())

            scenario_summaries.append(
                {
                    "scenario_id": str(scenario_id),
                    "scenario_type": str(s_type),
                    "rows": len(group),
                    "baseline_fraud_rate": round(base_fraud, 4),
                    "spike_fraud_rate": round(spk_fraud, 4),
                    "baseline_volume": base_vol,
                    "spike_volume": spk_vol,
                    "max_velocity_ratio": round(max_vel, 2),
                    "fraud_spike_label": label,
                }
            )

        scenario_splits = df_b.groupby("scenario_id")["split"].nunique()
        scenario_leakage = int((scenario_splits > 1).sum())

        dup_b_ids = (
            int(df_b["transaction_id"].duplicated().sum())
            if "transaction_id" in df_b.columns
            else 0
        )
        missing_b_times = int(df_b["event_time"].isna().sum())
        negative_b_amounts = int((df_b["amount"] < 0).sum())

        report["dataset_b"] = {
            "total_rows": len(df_b),
            "total_scenarios": int(df_b["scenario_id"].nunique()),
            "scenario_summary_table": scenario_summaries,
            "split_counts": {
                str(k): int(v) for k, v in df_b["split"].value_counts().to_dict().items()
            },
            "checks": {
                "no_duplicate_ids": dup_b_ids == 0,
                "no_missing_event_time": missing_b_times == 0,
                "no_negative_amounts": negative_b_amounts == 0,
                "no_scenario_leakage": scenario_leakage == 0,
            },
        }

    report_path = PROCESSED_DIR / "validation_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RazorShield data acquisition and synthetic scenario pipeline."
    )

    parser.add_argument(
        "--download-public",
        action="store_true",
        help="Download IEEE-CIS training files from Kaggle.",
    )

    parser.add_argument(
        "--build-model",
        action="store_true",
        help="Build Dataset A from IEEE-CIS.",
    )

    parser.add_argument(
        "--generate-scenarios",
        action="store_true",
        help="Generate Dataset B using NVIDIA + deterministic simulation.",
    )

    parser.add_argument(
        "--offline-synthetic",
        action="store_true",
        help="Use local fallback scenario specs instead of NVIDIA.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run download + Dataset A + Dataset B.",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Concurrent NVIDIA requests. Keep conservative for hosted APIs.",
    )

    parser.add_argument(
        "--scenarios",
        type=int,
        default=DEFAULT_SCENARIOS,
        help="Number of synthetic scenarios.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Scenario specs requested per NVIDIA API call.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
    )

    parser.add_argument(
        "--force-download",
        action="store_true",
    )

    return parser.parse_args()


def main() -> None:
    load_environment()
    args = parse_args()
    ensure_dirs()

    if not any(
        [
            args.download_public,
            args.build_model,
            args.generate_scenarios,
            args.all,
        ]
    ):
        print(
            "Nothing selected. Use --all or one of "
            "--download-public / --build-model / --generate-scenarios."
        )
        return

    tx_path = RAW_DIR / "train_transaction.csv"
    id_path = RAW_DIR / "train_identity.csv"

    model_path = None
    scenario_path = None
    specs_path = None

    if args.all or args.download_public or args.build_model:
        tx_path, id_path = download_ieee_cis(
            force=args.force_download
        )

    if args.all or args.build_model:
        model_path = build_model_dataset(
            tx_path,
            id_path,
            seed=args.seed,
        )

    if args.all or args.generate_scenarios:
        specs = generate_scenario_specs(
            count=args.scenarios,
            workers=args.workers,
            batch_size=args.batch_size,
            seed=args.seed,
            offline=args.offline_synthetic,
        )

        specs_path = save_specs(specs)
        scenario_path = generate_synthetic_dataset(specs)

    metadata_path = write_metadata(
        model_path,
        scenario_path,
        specs_path,
    )

    val_report_path = generate_validation_report(
        model_path,
        scenario_path,
    )

    LOGGER.info("Metadata written: %s", metadata_path)
    LOGGER.info("Validation report written: %s", val_report_path)
    LOGGER.info("Pipeline complete.")


if __name__ == "__main__":
    main()
