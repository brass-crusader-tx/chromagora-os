"""Model router — LLM integration layer for Chromagora OS.

Routes completion requests to the appropriate model tier via OpenRouter.
Free models only. No hardcoded API keys.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model tier configuration
# ---------------------------------------------------------------------------

MODEL_TIER_MAP: dict[int, str] = {
    1: "openrouter/google/gemma-4-26b-a4b-it:free",
    2: "openrouter/qwen/qwen3-coder:free",
    3: "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
}

DEFAULT_TEMPERATURE = 0.0
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_TOKENS = 2048

OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def complete_text(
    prompt: str,
    model_hint: Optional[str] = None,
    model_tier: Optional[int] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, Any]:
    """Complete text using the appropriate model.

    Args:
        prompt: The input prompt.
        model_hint: Optional model ID override.
        model_tier: Model tier (1-3). Tier 0 returns empty (deterministic).
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.

    Returns:
        Dict with 'content', 'model', 'tier', 'usage', 'latency_ms'.
    """
    if model_tier == 0:
        return {
            "content": "",
            "model": "none",
            "tier": 0,
            "usage": {},
            "latency_ms": 0,
        }

    model = model_hint or MODEL_TIER_MAP.get(model_tier, MODEL_TIER_MAP[1])

    if not OPENROUTER_API_KEY:
        return _mock_complete(prompt, model, model_tier, "no_api_key")

    try:
        return _call_openrouter(prompt, model, temperature, max_tokens, model_tier)
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return {
            "content": "",
            "model": model,
            "tier": model_tier,
            "error": str(exc),
            "latency_ms": 0,
        }


def complete_structured(
    prompt: str,
    schema: dict[str, Any],
    model_hint: Optional[str] = None,
    model_tier: Optional[int] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, Any]:
    """Complete structured output using the appropriate model.

    Args:
        prompt: The input prompt.
        schema: JSON Schema for the expected output.
        model_hint: Optional model ID override.
        model_tier: Model tier (1-3).
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.

    Returns:
        Dict with 'content' (parsed JSON), 'raw', 'model', 'tier', 'usage'.
    """
    if model_tier == 0:
        return {
            "content": {},
            "raw": "{}",
            "model": "none",
            "tier": 0,
            "usage": {},
            "latency_ms": 0,
        }

    # Augment prompt with schema instructions
    structured_prompt = _build_structured_prompt(prompt, schema)

    result = complete_text(
        prompt=structured_prompt,
        model_hint=model_hint,
        model_tier=model_tier,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Try to parse the response as JSON
    raw = result.get("content", "")
    try:
        parsed = json.loads(raw)
        result["content"] = parsed
        result["raw"] = raw
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse structured output as JSON")
        result["content"] = {}
        result["raw"] = raw

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _call_openrouter(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    tier: int,
) -> dict[str, Any]:
    """Make an API call to OpenRouter."""
    start = time.monotonic()

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    with httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
        resp = client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    elapsed_ms = int((time.monotonic() - start) * 1000)

    choice = data.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content", "")
    usage = data.get("usage", {})

    return {
        "content": content,
        "model": model,
        "tier": tier,
        "usage": usage,
        "latency_ms": elapsed_ms,
    }


def _mock_complete(
    prompt: str,
    model: str,
    tier: int,
    reason: str,
) -> dict[str, Any]:
    """Return a mock response when no API key is configured."""
    logger.info("Using mock LLM provider (reason: %s)", reason)
    return {
        "content": f"[mock:{model}] {prompt[:100]}...",
        "model": model,
        "tier": tier,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        "latency_ms": 0,
        "mock": True,
        "mock_reason": reason,
    }


def _build_structured_prompt(prompt: str, schema: dict[str, Any]) -> str:
    """Build a prompt that instructs the model to produce structured JSON."""
    schema_json = json.dumps(schema, indent=2)
    return (
        f"{prompt}\n\n"
        "You must respond with valid JSON matching this schema:\n"
        f"```json\n{schema_json}\n```\n"
        "Respond with ONLY the JSON, no other text."
    )
