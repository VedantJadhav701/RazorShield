"""
model_loader.py
---------------
NVIDIA Build API Client for RazorShield SLM Explainer.
Operates 100% via API (Zero GPU / Zero Local Model Weight Overhead).
"""

from __future__ import annotations

import os
import logging
from typing import Any

HAS_SPACES = False
LOGGER = logging.getLogger("slm-model-loader")


class SLMModelLoader:
    """NVIDIA Build API model loader for zero-shot explanation generation."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ):
        if os.getenv("NVIDIA_API_KEY") and os.getenv("NVIDIA_API_KEY").strip():
            if not model_name or "Qwen" in model_name:
                model_name = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")
        self.model_name = model_name or os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")
        self.max_tokens = max_new_tokens or int(os.getenv("SLM_MAX_TOKENS", "4096"))
        self.temperature = temperature or float(os.getenv("SLM_TEMPERATURE", "1.0"))
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Returns True if NVIDIA_API_KEY environment variable is configured."""
        key = os.getenv("NVIDIA_API_KEY", "").strip()
        return bool(key) or self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value: bool):
        self._is_loaded = value

    def load_model(self) -> bool:
        """Validates NVIDIA Build API configuration."""
        key = os.getenv("NVIDIA_API_KEY", "").strip()
        if key:
            LOGGER.info("NVIDIA_API_KEY detected. Active SLM: NVIDIA Build API (%s).", self.model_name)
            self._is_loaded = True
            return True

        LOGGER.warning("NVIDIA_API_KEY is not set. SLM will fall back to Deterministic Explainer (0 GPU).")
        self._is_loaded = False
        return False

    def generate(self, prompt: str) -> str:
        """Generates response using NVIDIA Build API (openai/gpt-oss-20b)."""
        nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
        if not nvidia_key:
            raise RuntimeError("Model is not loaded. Please set NVIDIA_API_KEY environment variable.")

        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=nvidia_key,
            )
            LOGGER.info("Executing SLM generation via NVIDIA Build API (%s)...", self.model_name)
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                top_p=1,
                max_tokens=self.max_tokens,
                stream=False,
            )
            reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
            if reasoning:
                LOGGER.info("NVIDIA Build API reasoning trace: %s", reasoning[:200])

            content = completion.choices[0].message.content
            if content and content.strip():
                return content.strip()
            raise RuntimeError("NVIDIA Build API returned empty response content.")
        except Exception as exc:
            LOGGER.error("NVIDIA Build API call failed: %s", exc)
            raise exc
