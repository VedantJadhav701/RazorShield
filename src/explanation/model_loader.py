"""
model_loader.py
---------------
Hugging Face Transformers model loader with ZeroGPU (@spaces.GPU) compatibility.
Supports automatic device detection (CUDA/CPU) and float16 precision.
"""

from __future__ import annotations

import os
import logging
from typing import Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    import spaces
    HAS_SPACES = True
except ImportError:
    HAS_SPACES = False
    spaces = None

LOGGER = logging.getLogger("slm-model-loader")


def _run_slm_generation(model, tokenizer, inputs, max_new_tokens: int, temperature: float):
    """Core CausalLM generation execution function executed inside GPU context."""
    target_device = "cuda" if torch.cuda.is_available() else "cpu"
    cuda_inputs = {k: v.to(target_device) for k, v in inputs.items()}
    with torch.no_grad():
        output_tokens = model.generate(
            **cuda_inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=False if temperature < 0.05 else True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    return output_tokens


if HAS_SPACES and spaces is not None:
    @spaces.GPU
    def _gpu_generate_wrapper(model, tokenizer, inputs, max_new_tokens: int, temperature: float):
        return _run_slm_generation(model, tokenizer, inputs, max_new_tokens, temperature)
else:
    def _gpu_generate_wrapper(model, tokenizer, inputs, max_new_tokens: int, temperature: float):
        return _run_slm_generation(model, tokenizer, inputs, max_new_tokens, temperature)


class SLMModelLoader:
    """Loads Hugging Face Small Language Models for zero-shot explanation generation."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ):
        self.model_name = model_name or os.getenv("SLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
        
        if device:
            self.device_str = device
        elif HAS_SPACES:
            self.device_str = "cuda"
        else:
            self.device_str = "cuda" if torch.cuda.is_available() else "cpu"

        self.max_new_tokens = max_new_tokens or int(os.getenv("SLM_MAX_NEW_TOKENS", "160"))
        self.temperature = temperature or float(os.getenv("SLM_TEMPERATURE", "0.1"))

        self.tokenizer = None
        self.model = None
        self.is_loaded = False

    def load_model(self) -> bool:
        """Loads tokenizer and CausalLM weights into memory."""
        LOGGER.info("Loading SLM candidate '%s' on device '%s' (ZeroGPU: %s) ...", self.model_name, self.device_str, HAS_SPACES)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            dtype = torch.float16 if self.device_str == "cuda" or HAS_SPACES else torch.float32

            if HAS_SPACES:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=dtype,
                    trust_remote_code=True,
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=dtype,
                    device_map="auto" if self.device_str == "cuda" else None,
                    trust_remote_code=True,
                )

                if self.device_str == "cpu":
                    self.model = self.model.to("cpu")

            self.model.eval()
            self.is_loaded = True
            LOGGER.info("Successfully loaded '%s' into memory.", self.model_name)
            return True
        except Exception as e:
            LOGGER.error("Failed to load model '%s': %s", self.model_name, e)
            self.is_loaded = False
            return False

    def generate(self, prompt: str) -> str:
        """Generates raw response text using ZeroGPU wrapper or CPU fallback."""
        if not self.is_loaded or self.model is None or self.tokenizer is None:
            raise RuntimeError("Model is not loaded. Call load_model() first.")

        inputs = self.tokenizer(prompt, return_tensors="pt")

        output_tokens = _gpu_generate_wrapper(
            self.model,
            self.tokenizer,
            inputs,
            self.max_new_tokens,
            self.temperature,
        )

        input_length = inputs["input_ids"].shape[1]
        generated_tokens = output_tokens[0][input_length:]
        text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return text
