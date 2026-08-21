"""
explainer.py
------------
RazorShield Explanation Generator Orchestrator.

Combines zero-shot SLM generation with strict deterministic grounding validation
and fallback execution.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from src.explanation.fallback import DeterministicFallbackExplainer
from src.explanation.model_loader import SLMModelLoader
from src.explanation.prompts import build_explanation_prompt
from src.explanation.schemas import ExplanationInput, ExplanationOutput, GoldExpectation
from src.explanation.validator import GroundingValidator

LOGGER = logging.getLogger("explanation-generator")


class RazorShieldExplainer:
    """Orchestrates zero-shot SLM explanation generation with strict grounding validation."""

    def __init__(self, model_loader: SLMModelLoader | None = None):
        self.loader = model_loader
        self.validator = GroundingValidator()

    def generate_explanation(
        self,
        input_data: ExplanationInput,
        expectation: GoldExpectation | None = None,
    ) -> tuple[ExplanationOutput, dict[str, Any]]:
        """
        Generates grounded explanation. If model fails or output violates grounding rules,
        fallbacks to deterministic template explanation without modifying risk decisions.
        """
        start_time = time.perf_counter()

        if self.loader is None or not self.loader.is_loaded:
            LOGGER.info("SLM model not loaded. Executing deterministic fallback ...")
            fallback_out = DeterministicFallbackExplainer.generate_fallback_explanation(
                input_data, failure_reason="Model unavailable"
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            val_res = self.validator.validate_grounding(input_data, fallback_out, expectation)
            val_res["latency_ms"] = round(elapsed_ms, 2)
            val_res["used_fallback"] = True
            val_res["fallback_reason"] = "Model unavailable"
            return fallback_out, val_res

        prompt = build_explanation_prompt(input_data)

        try:
            raw_text = self.loader.generate(prompt)
            parsed_out, json_errors = self.validator.parse_and_validate_json(raw_text)

            if parsed_out is None:
                LOGGER.warning("SLM output failed JSON/schema validation: %s. Using fallback.", json_errors)
                fallback_out = DeterministicFallbackExplainer.generate_fallback_explanation(
                    input_data, failure_reason=f"JSON validation failed: {json_errors[0] if json_errors else ''}"
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                val_res = self.validator.validate_grounding(input_data, fallback_out, expectation)
                val_res["latency_ms"] = round(elapsed_ms, 2)
                val_res["used_fallback"] = True
                val_res["fallback_reason"] = f"JSON validation failed: {json_errors}"
                return fallback_out, val_res

            # Run deterministic grounding checks
            val_res = self.validator.validate_grounding(input_data, parsed_out, expectation)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            val_res["latency_ms"] = round(elapsed_ms, 2)
            val_res["used_fallback"] = False

            if not val_res["passed"]:
                LOGGER.warning("SLM output violated grounding rules: %s. Using fallback.", val_res["errors"])
                fallback_out = DeterministicFallbackExplainer.generate_fallback_explanation(
                    input_data, failure_reason=f"Grounding failed: {val_res['errors'][0] if val_res['errors'] else ''}"
                )
                val_res["used_fallback"] = True
                val_res["fallback_reason"] = f"Grounding failed: {val_res['errors']}"
                return fallback_out, val_res

            return parsed_out, val_res

        except Exception as e:
            LOGGER.error("Exception during SLM explanation generation: %s. Using fallback.", e)
            fallback_out = DeterministicFallbackExplainer.generate_fallback_explanation(
                input_data, failure_reason=f"Execution exception: {e}"
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            val_res = self.validator.validate_grounding(input_data, fallback_out, expectation)
            val_res["latency_ms"] = round(elapsed_ms, 2)
            val_res["used_fallback"] = True
            val_res["fallback_reason"] = f"Execution exception: {e}"
            return fallback_out, val_res
