"""
validator.py
------------
Deterministic grounding and consistency validator for SLM generated explanations.
Checks JSON schema, decision consistency, severity consistency, numeric grounding,
campaign consistency, unsupported claims / hallucinations, and word count.
"""

from __future__ import annotations

import json
import re
from typing import Any
from src.explanation.schemas import ExplanationInput, ExplanationOutput, GoldExpectation


class GroundingValidator:
    """Deterministic grounding and consistency validator."""

    UNSUPPORTED_PATTERNS = [
        r"\$\d+(?:,\d+)*(?:\.\d+)?",  # Monetary amounts like $50,000 not in evidence
        r"\b(?:IP|geolocation|GPS|location|device_fingerprint)\b",  # Invented technical metadata
        r"\b(?:phishing|skimming|credential_stuffing|bin_attack)\b",  # Invented attack techniques
        r"\b(?:confirmed_fraud|guaranteed_fraud|100%_fraud)\b",  # Claiming certainty not in evidence
    ]

    def parse_and_validate_json(self, raw_text: str) -> tuple[ExplanationOutput | None, list[str]]:
        """Parses raw text into JSON and validates against ExplanationOutput Pydantic schema."""
        errors = []
        # Extract json chunk if wrapped in markdown code fence
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if json_match:
            text_to_parse = json_match.group(1)
        else:
            json_match_raw = re.search(r"(\{.*?\})", raw_text, re.DOTALL)
            text_to_parse = json_match_raw.group(1) if json_match_raw else raw_text

        try:
            data = json.loads(text_to_parse)
        except Exception as e:
            errors.append(f"JSON parsing error: {e}")
            return None, errors

        try:
            output = ExplanationOutput(**data)
            return output, errors
        except Exception as e:
            errors.append(f"Pydantic schema validation error: {e}")
            return None, errors

    def validate_grounding(
        self,
        input_data: ExplanationInput,
        output: ExplanationOutput,
        expectation: GoldExpectation | None = None,
    ) -> dict[str, Any]:
        """
        Executes strict deterministic grounding checks.
        Returns a detailed evaluation dictionary.
        """
        full_text = f"{output.title} {output.summary} {' '.join(output.key_signals)} {output.campaign_context} {output.recommended_action} {output.confidence_note}"
        full_text_lower = full_text.lower()
        words = full_text.split()
        word_count = len(words)

        # 1. Decision Consistency
        decision_consistent = True
        dec_errors = []
        if input_data.incident_state == "ALERT":
            if "normal activity" in full_text_lower or "no risk" in full_text_lower or "normal situation" in full_text_lower:
                decision_consistent = False
                dec_errors.append("ALERT state described as normal")
        elif input_data.incident_state == "INVESTIGATE":
            if "confirmed fraud" in full_text_lower or "normal activity" in full_text_lower:
                decision_consistent = False
                dec_errors.append("INVESTIGATE state described as confirmed fraud or normal")
        elif input_data.incident_state == "NORMAL":
            if "high risk incident" in full_text_lower or "severe attack" in full_text_lower:
                decision_consistent = False
                dec_errors.append("NORMAL state described as severe attack")

        # 2. Severity Consistency
        severity_consistent = True
        sev_errors = []
        if input_data.severity == "HIGH":
            if "low risk" in full_text_lower or "low severity" in full_text_lower or "minimal concern" in full_text_lower:
                severity_consistent = False
                sev_errors.append("HIGH severity described as low risk")
        elif input_data.severity == "LOW":
            if "high severity" in full_text_lower or "critical threat" in full_text_lower:
                severity_consistent = False
                sev_errors.append("LOW severity described as high severity")

        # 3. Campaign Consistency
        campaign_consistent = True
        camp_errors = []
        if input_data.campaign_active:
            if "no campaign" in full_text_lower or "inactive campaign" in full_text_lower or "no promo" in full_text_lower:
                campaign_consistent = False
                camp_errors.append("Active campaign claimed as inactive")
        else:
            if ("campaign is active" in full_text_lower and "no promotional campaign is active" not in full_text_lower and "no campaign is active" not in full_text_lower) or "promotional sale active" in full_text_lower:
                campaign_consistent = False
                camp_errors.append("Inactive campaign claimed as active")

        # 4. Numeric Grounding Check
        numeric_grounded = True
        num_errors = []

        # Verify fraud_excess_ratio preservation
        fe_val = input_data.fraud_excess_ratio
        # Match digits around decimal
        fe_matches = re.findall(rf"\b{fe_val:.1f}(?:x|0)?\b", full_text, re.IGNORECASE)
        # Check for contradictory numbers (e.g. claiming 3.2 when evidence says 8.2)
        fe_contradictions = re.findall(r"fraud excess(?: ratio)? (?:is|of) (\d+\.\d+)", full_text, re.IGNORECASE)
        for c_val in fe_contradictions:
            if abs(float(c_val) - fe_val) > 0.1:
                numeric_grounded = False
                num_errors.append(f"Contradictory fraud_excess_ratio {c_val} vs evidence {fe_val}")

        # 5. Unsupported Claims / Hallucination Detection
        hallucination_detected = False
        hallucination_errors = []

        for pattern in self.UNSUPPORTED_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                hallucination_detected = True
                hallucination_errors.append(f"Unsupported claim detected matching pattern '{pattern}': '{match.group(0)}'")

        if expectation:
            for forbidden in expectation.forbidden_claims:
                if forbidden.lower() in full_text_lower:
                    hallucination_detected = True
                    hallucination_errors.append(f"Forbidden claim present: '{forbidden}'")

        # 6. Word Count Check
        length_valid = word_count <= 150

        is_passed = (
            decision_consistent
            and severity_consistent
            and campaign_consistent
            and numeric_grounded
            and (not hallucination_detected)
            and length_valid
        )

        all_errors = dec_errors + sev_errors + camp_errors + num_errors + hallucination_errors
        if not length_valid:
            all_errors.append(f"Word count {word_count} exceeds maximum 150 words")

        return {
            "passed": is_passed,
            "word_count": word_count,
            "decision_consistent": decision_consistent,
            "severity_consistent": severity_consistent,
            "campaign_consistent": campaign_consistent,
            "numeric_grounded": numeric_grounded,
            "hallucination_detected": hallucination_detected,
            "length_valid": length_valid,
            "errors": all_errors,
        }
