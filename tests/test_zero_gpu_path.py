"""
test_zero_gpu_path.py
----------------------
Unit tests for ZeroGPU model loading wrapper and CPU fallback paths.
"""

import pytest
from src.explanation.model_loader import HAS_SPACES, SLMModelLoader


def test_model_loader_initialization():
    loader = SLMModelLoader(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    assert loader.model_name == "Qwen/Qwen2.5-0.5B-Instruct"
    # ZeroGPU import flag is boolean
    assert isinstance(HAS_SPACES, bool)


def test_cpu_fallback_path_when_unloaded():
    loader = SLMModelLoader(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    with pytest.raises(RuntimeError, match="Model is not loaded"):
        loader.generate("Test prompt")
