# RazorShield Hugging Face Space Deployment Guide

This document details the ZeroGPU architecture, environment setup, and deployment procedure for deploying RazorShield to Hugging Face Spaces (`vedantjadhav701/razorshield-api`).

---

## 1. ZeroGPU Deployment Strategy

The Space uses Hugging Face Spaces `spaces.GPU` decorator for dynamically allocated GPU acceleration:

- **CPU Workloads**: Request validation (`preprocessing.py`), feature adaptation (`adapter.py`), calibrated XGBoost inference (`decision_engine.py`), merchant rolling temporal state (`merchant_state.py`), persistent incident engine (`incident_engine.py`), grounding validation (`validator.py`), and template fallback generation (`fallback.py`).
- **ZeroGPU Workload**: CausalLM token generation using `Qwen/Qwen2.5-0.5B-Instruct` wrapped with `@spaces.GPU`.

---

## 2. Environment Variables

Supported environment configuration:

- `SLM_MODEL`: `Qwen/Qwen2.5-0.5B-Instruct` (default)
- `SLM_MAX_NEW_TOKENS`: `160` (default)
- `SLM_TEMPERATURE`: `0.1` (default)
- `POLICY_MODE`: `BALANCED` (default)

---

## 3. Git Deployment Steps to Hugging Face Space

To deploy this backend repository to Hugging Face Space `vedantjadhav701/razorshield-api`:

```bash
# 1. Add Hugging Face Space remote
git remote add hf https://huggingface.co/spaces/vedantjadhav701/razorshield-api

# 2. Push repository to Hugging Face Space
git push hf main
```
