"""
RazorShield — AI-Powered Merchant Fraud & Risk Intelligence System.

Hugging Face Space Backend Application powered by Gradio and NVIDIA NIM API.

Architecture:

    Vercel Next.js Frontend
            |
            | HTTPS / Gradio API
            v
    Hugging Face Space
            |
            +-- CPU Risk Pipeline
            |     +-- preprocessing
            |     +-- calibrated XGBoost
            |     +-- merchant temporal state
            |     +-- incident engine
            |     +-- policy engine
            |
            +-- NVIDIA NIM API
                  +-- openai/gpt-oss-20b
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import time
from typing import Any

import gradio as gr
import pandas as pd

from src.api.schemas import (
    AnalyzeTransactionResponse,
    CampaignInfoResponse,
    DecisionResponse,
    MerchantRiskResponse,
    PerformanceMetricsResponse,
    TransactionRiskResponse,
)

from src.explanation.fallback import DeterministicFallbackExplainer
from src.explanation.schemas import ExplanationInput

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.incident.incident_engine import MerchantIncidentEngine

from src.inference.adapter import InferenceAdapter
from src.inference.preprocessing import validate_raw_api_payload

from src.risk_engine.campaign import CampaignRegistration
from src.risk_engine.schemas import TransactionInput


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

LOGGER = logging.getLogger("razorshield-app")


# =============================================================================
# Environment
# =============================================================================

SLM_MODEL_NAME = os.getenv(
    "NVIDIA_MODEL",
    os.getenv("SLM_MODEL", "openai/gpt-oss-20b"),
)

POLICY_MODE_DEFAULT = os.getenv(
    "POLICY_MODE",
    "BALANCED",
)

APP_VERSION = os.getenv(
    "RAZORSHIELD_VERSION",
    "phase-9-integration",
)


# =============================================================================
# Engine Initialization
# =============================================================================

LOGGER.info("Initializing RazorShield engines...")

INCIDENT_ENGINE = MerchantIncidentEngine(
    policy_mode=POLICY_MODE_DEFAULT,
    persistence_n=2,
)

INFERENCE_ADAPTER = InferenceAdapter()


# =============================================================================
# ZeroGPU Space Compatibility Hook
# =============================================================================

try:
    import spaces

    @spaces.GPU
    def _zero_gpu_startup_check():
        """Satisfies HF ZeroGPU runtime detector on startup without consuming GPU."""
        return True

    _zero_gpu_startup_check()
    LOGGER.info("ZeroGPU compatibility hook registered and initialized.")
except Exception:
    def _zero_gpu_startup_check():
        return True


# =============================================================================
# NVIDIA NIM Explanation Layer
# =============================================================================

NVIDIA_BASE_URL = os.getenv(
    "NVIDIA_BASE_URL",
    "https://integrate.api.nvidia.com/v1",
)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()

SLM_MODEL_NAME = os.getenv(
    "NVIDIA_MODEL",
    "openai/gpt-oss-20b",
)

NVIDIA_TIMEOUT_SECONDS = float(
    os.getenv("NVIDIA_TIMEOUT_SECONDS", "30")
)

NVIDIA_CLIENT = None
SLM_LOADED = False

if OpenAI is None:
    LOGGER.warning("OpenAI SDK is not installed; deterministic explanation fallback will be used.")
elif NVIDIA_API_KEY:
    NVIDIA_CLIENT = OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY,
    )
    # NVIDIA API models are remote; there is no local model-loading step.
    SLM_LOADED = True
    LOGGER.info(
        "NVIDIA NIM explanation client configured | model=%s",
        SLM_MODEL_NAME,
    )
else:
    LOGGER.warning(
        "NVIDIA_API_KEY is not configured; deterministic explanation fallback will be used."
    )

# =============================================================================
# Grounded NVIDIA Explanation Helper
# =============================================================================

def _generate_explanation(exp_input: ExplanationInput) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Convert deterministic RazorShield evidence into a concise grounded explanation.

    IMPORTANT:
    - The NVIDIA model never determines the risk decision.
    - All risk values originate from the deterministic engines.
    - The model is only allowed to verbalize supplied evidence.
    - If NVIDIA is unavailable or output fails grounding checks, use the
      deterministic fallback explainer.
    """
    if NVIDIA_CLIENT is None:
        fallback = DeterministicFallbackExplainer.generate_fallback_explanation(
            exp_input,
            failure_reason="NVIDIA_API_KEY/OpenAI client unavailable",
        )
        return (
            fallback.model_dump(),
            {
                "valid": True,
                "method": "deterministic_fallback",
                "reason": "NVIDIA API unavailable",
            },
        )

    evidence = exp_input.model_dump()

    system_prompt = """You are RazorShield's evidence explanation engine.

Your ONLY task is to convert supplied deterministic fraud-risk evidence into a concise,
grounded explanation for a merchant risk operator.

CRITICAL RULES:
1. Never make or change the risk decision.
2. Never invent facts, amounts, customers, transactions, causes, or signals.
3. Use ONLY values present in the evidence JSON.
4. Preserve decision, incident state, severity, campaign status, and numeric values.
5. Do not describe the output as a probability unless the supplied field is explicitly
   a probability.
6. Explain why the deterministic engine reached its decision using the supplied signals.
7. Keep the explanation concise: 40-100 words.
8. Return JSON only with exactly these keys:
   summary, decision, severity, evidence
9. "decision" must exactly equal recommended_action.
10. "severity" must exactly equal severity from the evidence.
11. "evidence" must be a short array of strings containing only grounded facts.
"""

    user_prompt = (
        "Convert the following deterministic RazorShield evidence into the required JSON.\n\n"
        + json.dumps(evidence, ensure_ascii=False, default=str)
    )

    try:
        completion = NVIDIA_CLIENT.chat.completions.create(
            model=SLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            top_p=1,
            max_tokens=500,
            stream=False,
            timeout=NVIDIA_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content or ""
        generated = json.loads(content)

        # ---- Deterministic grounding validation ----
        if not isinstance(generated, dict):
            raise ValueError("NVIDIA output is not a JSON object")

        required = {"summary", "decision", "severity", "evidence"}
        if not required.issubset(generated):
            raise ValueError("NVIDIA output is missing required explanation fields")

        if str(generated["decision"]) != str(exp_input.recommended_action):
            raise ValueError("Generated decision contradicts deterministic decision")

        if str(generated["severity"]) != str(exp_input.severity):
            raise ValueError("Generated severity contradicts deterministic severity")

        if not isinstance(generated["evidence"], list):
            raise ValueError("Generated evidence must be a list")

        # Basic numeric grounding: every numeric token used by the model must occur
        # in the supplied evidence. This intentionally errs on the safe side.
        source_numbers = set()
        for value in evidence.values():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                source_numbers.add(str(value))
                source_numbers.add(f"{float(value):g}")

        generated_text = json.dumps(generated, ensure_ascii=False)
        import re
        output_numbers = re.findall(
            r"(?<![A-Za-z])(?:\\d+(?:\\.\\d+)?)(?![A-Za-z])",
            generated_text,
        )

        for number in output_numbers:
            if not any(
                number == candidate
                or number.rstrip("0").rstrip(".") == candidate.rstrip("0").rstrip(".")
                for candidate in source_numbers
            ):
                raise ValueError(
                    f"Generated numeric value '{number}' is not grounded in evidence"
                )

        return (
            generated,
            {
                "valid": True,
                "method": "nvidia_nim",
                "model": SLM_MODEL_NAME,
            },
        )

    except Exception as exc:
        LOGGER.exception("NVIDIA explanation failed; using deterministic fallback.")

        fallback = DeterministicFallbackExplainer.generate_fallback_explanation(
            exp_input,
            failure_reason=str(exc),
        )

        return (
            fallback.model_dump(),
            {
                "valid": True,
                "method": "deterministic_fallback",
                "reason": str(exc),
            },
        )


# =============================================================================
# Utility Functions
# =============================================================================

def _json_response(payload: Any) -> str:
    """
    Serialize API response consistently.
    """
    return json.dumps(
        payload,
        indent=2,
        default=str,
    )


# =============================================================================
# Public API: Health
# =============================================================================

def health_check() -> str:
    """
    Lightweight backend health/status endpoint.

    This endpoint does not execute the risk engine or consume NVIDIA NIM API.

    Exposed as:
        api_name="health_check"
    """

    return _json_response(
        {
            "status": "healthy",
            "service": "razorshield-api",
            "version": APP_VERSION,
            "backend": "huggingface-spaces-nvidia-nim",
            "risk_engine": "READY",
            "incident_engine": "READY",
            "slm": {
                "model": SLM_MODEL_NAME,
                "configured": bool(NVIDIA_CLIENT),
                "status": "READY" if NVIDIA_CLIENT else "FALLBACK",
                "execution": "NVIDIA_NIM_API",
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


# =============================================================================
# Public API: Analyze Transaction
# =============================================================================

def analyze_transaction(
    merchant_id: str,
    transaction_id: str,
    customer_id: str = "C_UNKNOWN",
    device_id: str = "D_UNKNOWN",
    event_time: str = "",
    amount: float = 100.0,
    payment_method: str = "card",
    transaction_type: str = "sale",
    policy_mode: str = "BALANCED",
) -> str:
    """
    Analyze a single transaction through the complete RazorShield pipeline.

    Pipeline:

        Validation
            ↓
        Calibrated Transaction Risk
            ↓
        Merchant Temporal State
            ↓
        Spike Detection
            ↓
        Incident Persistence
            ↓
        Policy Decision
            ↓
        Grounded Explanation

    Exposed as:
        api_name="analyze_transaction"
    """

    t_start_total = time.perf_counter()

    # -------------------------------------------------------------------------
    # Event time
    # -------------------------------------------------------------------------

    if not event_time or not str(event_time).strip():
        event_time = datetime.now().isoformat()

    # -------------------------------------------------------------------------
    # Raw payload
    # -------------------------------------------------------------------------

    raw_payload = {
        "merchant_id": merchant_id,
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "device_id": device_id,
        "event_time": event_time,
        "amount": amount,
        "payment_method": payment_method,
        "transaction_type": transaction_type,
        "policy_mode": policy_mode,
    }

    # -------------------------------------------------------------------------
    # 1. Validation
    # -------------------------------------------------------------------------

    try:
        api_input = validate_raw_api_payload(raw_payload)

    except ValueError as val_err:

        LOGGER.warning(
            "Transaction validation failed: %s",
            val_err,
        )

        return _json_response(
            {
                "error": "Validation Error",
                "details": str(val_err),
            }
        )

    # -------------------------------------------------------------------------
    # 2. Risk + Incident Engine
    # -------------------------------------------------------------------------

    t_start_risk = time.perf_counter()

    tx_input = TransactionInput(
        transaction_id=api_input.transaction_id,
        merchant_id=api_input.merchant_id,
        customer_id=api_input.customer_id,
        device_id=api_input.device_id,
        event_time=api_input.event_time,
        amount=api_input.amount,
        payment_method=api_input.payment_method,
        transaction_type=api_input.transaction_type,
    )

    tx_dec, inc_dec = INCIDENT_ENGINE.process_transaction(
        tx_input
    )

    t_risk_ms = (
        time.perf_counter() - t_start_risk
    ) * 1000.0

    # -------------------------------------------------------------------------
    # 3. Explanation Layer
    # -------------------------------------------------------------------------

    t_start_slm = time.perf_counter()

    slm_ms = 0.0

    exp_input = ExplanationInput(
        merchant_id=api_input.merchant_id,
        incident_state=inc_dec["incident_state"],
        severity=inc_dec["severity"],
        incident_score=inc_dec["incident_score"],
        spike_probability=inc_dec["spike_probability"],
        fraud_excess_ratio=inc_dec["fraud_excess_ratio"],
        velocity_ratio=inc_dec["velocity_ratio"],
        suspicious_windows=inc_dec["suspicious_windows"],
        total_suspicious_windows=inc_dec["total_suspicious_windows"],
        campaign_active=inc_dec["campaign_active"],
        policy_mode=api_input.policy_mode,
        signals=inc_dec["signals"],
        recommended_action=tx_dec.decision,
    )

    if inc_dec["incident_state"] in ["INVESTIGATE", "ALERT"]:
        exp_json, val_res = _generate_explanation(exp_input)
        slm_ms = (
            time.perf_counter() - t_start_slm
        ) * 1000.0
    else:
        exp_out = DeterministicFallbackExplainer.generate_fallback_explanation(
            exp_input,
            failure_reason="Deterministic processing (Normal risk)",
        )
        exp_json = exp_out.model_dump()
        val_res = {
            "valid": True,
            "method": "deterministic_fallback",
            "reason": "Normal risk state",
        }

    # -------------------------------------------------------------------------
    # 4. Total latency
    # -------------------------------------------------------------------------

    t_total_ms = (
        time.perf_counter()
        - t_start_total
    ) * 1000.0

    # -------------------------------------------------------------------------
    # 5. Structured response
    # -------------------------------------------------------------------------

    resp = AnalyzeTransactionResponse(
        transaction_id=api_input.transaction_id,
        merchant_id=api_input.merchant_id,

        transaction_risk=TransactionRiskResponse(
            fraud_probability=tx_dec.calibrated_fraud_probability,
        ),

        merchant_risk=MerchantRiskResponse(
            spike_probability=inc_dec["spike_probability"],
            fraud_excess_ratio=inc_dec["fraud_excess_ratio"],
            velocity_ratio=inc_dec["velocity_ratio"],
            incident_state=inc_dec["incident_state"],
            severity=inc_dec["severity"],
            incident_score=inc_dec["incident_score"],
            suspicious_windows=inc_dec["suspicious_windows"],
        ),

        campaign=CampaignInfoResponse(
            active=inc_dec["campaign_active"],
            campaign_name=(
                "PROMOTIONAL_SALE"
                if inc_dec["campaign_active"]
                else None
            ),
        ),

        decision=DecisionResponse(
            action=tx_dec.decision,
            policy_mode=api_input.policy_mode,
        ),

        explanation=exp_json,

        performance=PerformanceMetricsResponse(
            risk_engine_latency_ms=round(
                t_risk_ms,
                3,
            ),
            slm_latency_ms=round(
                slm_ms,
                3,
            ),
            total_latency_ms=round(
                t_total_ms,
                3,
            ),
        ),
    )

    return _json_response(
        resp.model_dump()
    )


# =============================================================================
# Public API: Merchant State
# =============================================================================

def analyze_merchant(
    merchant_id: str,
) -> str:
    """
    Return live merchant temporal state.

    Exposed as:
        api_name="analyze_merchant"
    """

    if not merchant_id or not str(merchant_id).strip():

        return _json_response(
            {
                "error": "Validation Error",
                "details": "Missing merchant_id",
            }
        )

    m_id = str(merchant_id).strip()

    m_state = (
        INCIDENT_ENGINE
        .risk_engine
        .state_manager
        .get_state(m_id)
    )

    inc_state = (
        INCIDENT_ENGINE
        .get_incident_state(m_id)
    )

    result = {
        "merchant_id": m_id,

        "rolling_window": {
            "rolling_txn_count_15m": (
                m_state.rolling_15m_volume
            ),

            "baseline_txn_count_15m": (
                m_state.baseline_txn_15m
            ),

            "velocity_ratio": round(
                m_state.velocity_ratio,
                2,
            ),

            "estimated_fraud_count": round(
                m_state.calibrated_estimated_fraud_count,
                4,
            ),

            "expected_fraud_count": round(
                m_state.expected_fraud_count,
                4,
            ),

            "fraud_excess_ratio": round(
                m_state.fraud_excess_ratio,
                2,
            ),
        },

        "incident_state": inc_state.to_dict(),
    }

    return _json_response(result)


# =============================================================================
# Public API: Scenario Replay
# =============================================================================

def run_scenario(
    scenario_name: str,
    policy_mode: str = "BALANCED",
) -> str:
    """
    Replay Dataset B test scenarios chronologically.

    Exposed as:
        api_name="run_scenario"
    """

    root_dir = Path(__file__).resolve().parent

    feat_path = (
        root_dir
        / "data"
        / "processed"
        / "dataset_b_features.parquet"
    )

    scenario_map = {
        "NORMAL": "normal",
        "VOLUME_ONLY_SPIKE": "volume_only_spike",
        "AMOUNT_SHIFT": "amount_shift",
        "FRAUD_SPIKE": "fraud_spike",
        "FRAUD_DURING_FLASH_SALE": "fraud_spike",
    }

    scenario_type = scenario_map.get(
        scenario_name.upper(),
        "normal",
    )

    json_path = (
        root_dir
        / "data"
        / "processed"
        / "demo_scenarios.json"
    )

    if feat_path.exists():
        df_b = pd.read_parquet(feat_path)
    elif json_path.exists():
        df_b = pd.read_json(json_path)
    else:
        return _json_response(
            {
                "error": "Demo scenario dataset missing"
            }
        )

    test_df = df_b[
        df_b["split"] == "test"
    ].copy()

    scenario_df = test_df[
        test_df["scenario_type"]
        == scenario_type
    ].copy()

    if len(scenario_df) == 0:

        return _json_response(
            {
                "error": (
                    f"No scenarios found for type "
                    f"'{scenario_type}'"
                )
            }
        )

    # Deterministic demo scenario
    first_scenario_id = (
        scenario_df["scenario_id"].iloc[0]
    )

    demo_txs = (
        scenario_df[
            scenario_df["scenario_id"]
            == first_scenario_id
        ]
        .sort_values("event_time")
    )

    merchant_id = str(
        demo_txs["merchant_id"].iloc[0]
    )

    # -------------------------------------------------------------------------
    # Campaign registration
    # -------------------------------------------------------------------------

    if (
        "FLASH_SALE"
        in scenario_name.upper()
        or scenario_name.upper()
        == "VOLUME_ONLY_SPIKE"
    ):

        min_t = demo_txs[
            "event_time"
        ].min()

        max_t = demo_txs[
            "event_time"
        ].max()

        INCIDENT_ENGINE.register_campaign(
            CampaignRegistration(
                merchant_id=merchant_id,
                campaign_name="DEMO_FLASH_SALE",
                start_time=min_t,
                end_time=max_t,
                expected_volume_multiplier=4.0,
            )
        )

    # -------------------------------------------------------------------------
    # Replay
    # -------------------------------------------------------------------------

    t_start = time.perf_counter()

    state_counts = {
        "NORMAL": 0,
        "INVESTIGATE": 0,
        "ALERT": 0,
    }

    last_tx_dec = None
    last_inc_dec = None

    for _, row in demo_txs.iterrows():

        tx_input = TransactionInput(
            transaction_id=str(
                row["transaction_id"]
            ),

            merchant_id=str(
                row["merchant_id"]
            ),

            customer_id=str(
                row.get(
                    "customer_id",
                    "C_DEMO",
                )
            ),

            device_id=str(
                row.get(
                    "device_id",
                    "D_DEMO",
                )
            ),

            event_time=row["event_time"],

            amount=float(
                row["amount"]
            ),

            payment_method="card",
            transaction_type="sale",
        )

        predicted_probability = float(
            row.get(
                "predicted_fraud_prob",
                0.01,
            )
        )

        (
            last_tx_dec,
            last_inc_dec,
        ) = INCIDENT_ENGINE.process_transaction(
            tx_input,
            calibrated_fraud_prob=predicted_probability,
        )

        state_counts[
            last_inc_dec["incident_state"]
        ] += 1

    elapsed_ms = (
        time.perf_counter()
        - t_start
    ) * 1000.0

    # -------------------------------------------------------------------------
    # Final explanation
    # -------------------------------------------------------------------------

    exp_input = ExplanationInput(
        merchant_id=merchant_id,
        incident_state=last_inc_dec["incident_state"],
        severity=last_inc_dec["severity"],
        incident_score=last_inc_dec["incident_score"],
        spike_probability=last_inc_dec["spike_probability"],
        fraud_excess_ratio=last_inc_dec["fraud_excess_ratio"],
        velocity_ratio=last_inc_dec["velocity_ratio"],
        suspicious_windows=last_inc_dec["suspicious_windows"],
        total_suspicious_windows=last_inc_dec["total_suspicious_windows"],
        campaign_active=last_inc_dec["campaign_active"],
        policy_mode=policy_mode,
        signals=last_inc_dec["signals"],
        recommended_action=(
            last_tx_dec.decision if last_tx_dec else "APPROVE"
        ),
    )

    exp_json, _ = _generate_explanation(exp_input)

    result = {
        "scenario_name": scenario_name,
        "scenario_id": first_scenario_id,
        "merchant_id": merchant_id,
        "total_transactions": len(demo_txs),
        "replay_time_ms": round(
            elapsed_ms,
            2,
        ),
        "incident_state_distribution": state_counts,
        "final_incident_state": (
            last_inc_dec["incident_state"]
        ),
        "final_severity": (
            last_inc_dec["severity"]
        ),
        "explanation": exp_json,
    }

    return _json_response(result)


# =============================================================================
# Public API: Direct Evidence Explanation
# =============================================================================

def explain_evidence(
    evidence_json: str,
) -> str:
    """
    Convert structured evidence into grounded SLM explanation.

    Exposed as:
        api_name="explain_evidence"
    """

    try:

        data = json.loads(
            evidence_json
        )

        exp_input = ExplanationInput(
            **data
        )

        exp_json, val_res = _generate_explanation(exp_input)

        result = {
            "explanation": exp_json,
            "validation": val_res,
        }

        return _json_response(result)

    except Exception as exc:

        LOGGER.exception(
            "Explanation generation failed."
        )

        return _json_response(
            {
                "error": "Explanation Generation Error",
                "details": str(exc),
            }
        )


# =============================================================================
# Public API: Reset
# =============================================================================

def reset_demo_state() -> str:
    """
    Reset all merchant temporal states,
    incident states and campaign registrations.

    Exposed as:
        api_name="reset_demo_state"
    """

    INCIDENT_ENGINE.reset_state()
    INFERENCE_ADAPTER.tracker.reset()

    return _json_response(
        {
            "status": "SUCCESS",
            "message": (
                "All merchant states and campaigns reset."
            ),
        }
    )


# =============================================================================
# Gradio Application
# =============================================================================

def build_gradio_app() -> gr.Blocks:
    """
    Construct the Gradio backend application.

    The Gradio UI exists primarily as:
        1. Space demonstration interface
        2. API endpoint exposure
        3. Manual backend verification
    """

    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="slate",
    )

    with gr.Blocks(
        theme=theme,
        title="RazorShield API & Risk Intelligence",
    ) as demo:

        gr.Markdown(
            """
# RazorShield — AI-Powered Merchant Fraud & Risk Intelligence

### Real-Time Calibrated Transaction Fraud,
Temporal Merchant Incident Detection &
Grounded NVIDIA SLM Explanation Layer

**Backend:** Hugging Face Spaces  
**Risk Engine:** Deterministic  
**SLM:** openai/gpt-oss-20b via NVIDIA NIM  
**Execution:** NVIDIA API (no local GPU required)
"""
        )

        # ---------------------------------------------------------------------
        # Health
        # ---------------------------------------------------------------------

        with gr.Tab("System Health"):

            gr.Markdown(
                "#### Live backend and SLM health status"
            )

            health_btn = gr.Button(
                "Check System Health",
                variant="primary",
            )

            health_out = gr.Code(
                language="json",
                label="Health Response",
            )

            health_btn.click(
                fn=health_check,
                inputs=[],
                outputs=[health_out],
                api_name="health_check",
            )

        # ---------------------------------------------------------------------
        # Transaction
        # ---------------------------------------------------------------------

        with gr.Tab("Transaction Risk Analysis"):

            gr.Markdown(
                """
#### Submit transaction payload for real-time risk assessment

The decision is produced by the deterministic risk engine.
The SLM only generates a grounded explanation.
"""
            )

            with gr.Row():

                with gr.Column():

                    m_id_in = gr.Textbox(
                        value="M_101",
                        label="Merchant ID",
                    )

                    tx_id_in = gr.Textbox(
                        value="TX_994182",
                        label="Transaction ID",
                    )

                    cust_id_in = gr.Textbox(
                        value="C_1048",
                        label="Customer ID",
                    )

                    dev_id_in = gr.Textbox(
                        value="D_882",
                        label="Device ID",
                    )

                    time_in = gr.Textbox(
                        value=datetime.now().isoformat(),
                        label="Event Time (ISO 8601)",
                    )

                    amt_in = gr.Number(
                        value=125.50,
                        label="Amount ($)",
                    )

                    pm_in = gr.Dropdown(
                        choices=[
                            "card",
                            "ach",
                            "crypto",
                            "paypal",
                        ],
                        value="card",
                        label="Payment Method",
                    )

                    tt_in = gr.Dropdown(
                        choices=[
                            "sale",
                            "transfer",
                            "refund",
                        ],
                        value="sale",
                        label="Transaction Type",
                    )

                    pol_in = gr.Dropdown(
                        choices=[
                            "CONSERVATIVE",
                            "BALANCED",
                            "HIGH_SENSITIVITY",
                        ],
                        value="BALANCED",
                        label="Policy Mode",
                    )

                    btn_analyze = gr.Button(
                        "Analyze Transaction",
                        variant="primary",
                    )

                with gr.Column():

                    tx_out = gr.Code(
                        language="json",
                        label="Structured API Response",
                    )

            btn_analyze.click(
                fn=analyze_transaction,
                inputs=[
                    m_id_in,
                    tx_id_in,
                    cust_id_in,
                    dev_id_in,
                    time_in,
                    amt_in,
                    pm_in,
                    tt_in,
                    pol_in,
                ],
                outputs=[tx_out],
                api_name="analyze_transaction",
            )

        # ---------------------------------------------------------------------
        # Scenario Replay
        # ---------------------------------------------------------------------

        with gr.Tab("Scenario Replay Demo"):

            gr.Markdown(
                """
#### Replay Dataset B test scenarios chronologically
"""
            )

            with gr.Row():

                with gr.Column():

                    sc_select = gr.Dropdown(
                        choices=[
                            "NORMAL",
                            "VOLUME_ONLY_SPIKE",
                            "AMOUNT_SHIFT",
                            "FRAUD_SPIKE",
                            "FRAUD_DURING_FLASH_SALE",
                        ],
                        value="FRAUD_SPIKE",
                        label="Select Demo Scenario",
                    )

                    sc_policy = gr.Dropdown(
                        choices=[
                            "CONSERVATIVE",
                            "BALANCED",
                            "HIGH_SENSITIVITY",
                        ],
                        value="BALANCED",
                        label="Policy Mode",
                    )

                    btn_run_sc = gr.Button(
                        "Run Scenario Replay",
                        variant="primary",
                    )

                with gr.Column():

                    sc_out = gr.Code(
                        language="json",
                        label="Scenario Execution Summary",
                    )

            btn_run_sc.click(
                fn=run_scenario,
                inputs=[
                    sc_select,
                    sc_policy,
                ],
                outputs=[sc_out],
                api_name="run_scenario",
            )

        # ---------------------------------------------------------------------
        # Merchant State
        # ---------------------------------------------------------------------

        with gr.Tab("Merchant Incident State"):

            gr.Markdown(
                """
#### Query live merchant temporal rolling state
"""
            )

            with gr.Row():

                with gr.Column():

                    m_query_in = gr.Textbox(
                        value="M_101",
                        label="Merchant ID",
                    )

                    btn_m_query = gr.Button(
                        "Query Merchant State",
                    )

                with gr.Column():

                    m_query_out = gr.Code(
                        language="json",
                        label="Merchant Incident State",
                    )

            btn_m_query.click(
                fn=analyze_merchant,
                inputs=[m_query_in],
                outputs=[m_query_out],
                api_name="analyze_merchant",
            )

        # ---------------------------------------------------------------------
        # SLM Explanation
        # ---------------------------------------------------------------------

        with gr.Tab("SLM Grounding Validator"):

            gr.Markdown(
                """
#### Convert structured risk evidence into a grounded explanation

The SLM does not determine the risk decision.
"""
            )

            with gr.Row():

                with gr.Column():

                    ev_in = gr.Code(
                        language="json",
                        value=json.dumps(
                            {
                                "merchant_id": "M_101",
                                "incident_state": "ALERT",
                                "severity": "HIGH",
                                "incident_score": 0.88,
                                "spike_probability": 0.92,
                                "fraud_excess_ratio": 8.2,
                                "velocity_ratio": 4.1,
                                "suspicious_windows": 3,
                                "total_suspicious_windows": 3,
                                "campaign_active": True,
                                "policy_mode": "BALANCED",
                                "signals": [
                                    {
                                        "name": "fraud_excess_ratio",
                                        "value": 8.2,
                                        "direction": "elevated",
                                    },
                                    {
                                        "name": "velocity_ratio",
                                        "value": 4.1,
                                        "direction": "suppressed",
                                    },
                                ],
                                "recommended_action": "ALERT",
                            },
                            indent=2,
                        ),
                        label="Structured Evidence Input",
                    )

                    btn_exp_ev = gr.Button(
                        "Generate SLM Explanation"
                    )

                with gr.Column():

                    ev_out = gr.Code(
                        language="json",
                        label="Grounded SLM Output",
                    )

            btn_exp_ev.click(
                fn=explain_evidence,
                inputs=[ev_in],
                outputs=[ev_out],
                api_name="explain_evidence",
            )

        # ---------------------------------------------------------------------
        # Reset
        # ---------------------------------------------------------------------

        with gr.Row():

            btn_reset = gr.Button(
                "Reset Demo State",
                variant="stop",
            )

            reset_out = gr.Textbox(
                label="Reset Status",
                interactive=False,
            )

        btn_reset.click(
            fn=reset_demo_state,
            inputs=[],
            outputs=[reset_out],
            api_name="reset_demo_state",
        )

    return demo


# =============================================================================
# Build Application
# =============================================================================

demo = build_gradio_app()


# =============================================================================
# Launch
# =============================================================================

if __name__ == "__main__":
    LOGGER.info("Starting RazorShield Gradio Space...")
    LOGGER.info(
        "NVIDIA explanation model=%s | API configured=%s | no local GPU required",
        SLM_MODEL_NAME,
        bool(NVIDIA_CLIENT),
    )

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
    )