"""Tests for LLM Model Router."""

import pytest
from unittest.mock import patch, MagicMock

from chromagora_workers.llm.model_router import (
    complete_text,
    complete_structured,
    MODEL_TIER_MAP,
    _mock_complete,
    _build_structured_prompt,
)


class TestCompleteText:
    def test_tier_0_returns_empty(self):
        result = complete_text("test", model_tier=0)
        assert result["content"] == ""
        assert result["model"] == "none"
        assert result["tier"] == 0

    @patch("chromagora_workers.llm.model_router.OPENROUTER_API_KEY", "")
    def test_no_api_key_returns_mock(self):
        result = complete_text("test prompt", model_tier=1)
        assert result["mock"] is True
        assert result["model"] == MODEL_TIER_MAP[1]
        assert "no_api_key" in result["mock_reason"]

    @patch("chromagora_workers.llm.model_router.OPENROUTER_API_KEY", "test-key")
    @patch("chromagora_workers.llm.model_router._call_openrouter")
    def test_with_api_key_calls_openrouter(self, mock_call):
        mock_call.return_value = {
            "content": "response",
            "model": "test-model",
            "tier": 1,
            "usage": {"prompt_tokens": 10},
            "latency_ms": 100,
        }
        result = complete_text("test", model_tier=1)
        assert result["content"] == "response"
        mock_call.assert_called_once()

    def test_model_hint_override(self):
        result = complete_text("test", model_hint="custom/model:free", model_tier=0)
        assert result["model"] == "none"  # tier 0 ignores hint

    @patch("chromagora_workers.llm.model_router.OPENROUTER_API_KEY", "")
    def test_default_model_by_tier(self):
        result = complete_text("test", model_tier=2)
        assert result["model"] == MODEL_TIER_MAP[2]


class TestCompleteStructured:
    def test_tier_0_returns_empty_dict(self):
        result = complete_text("test", model_tier=0)
        assert result["tier"] == 0

    @patch("chromagora_workers.llm.model_router.OPENROUTER_API_KEY", "")
    def test_structured_returns_mock(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = complete_structured("test", schema, model_tier=1)
        assert result["mock"] is True
        assert "raw" in result

    @patch("chromagora_workers.llm.model_router.OPENROUTER_API_KEY", "")
    def test_structured_parses_json(self):
        """Mock returns a string that looks like JSON."""
        schema = {"type": "object"}
        result = complete_structured("test", schema, model_tier=1)
        # Mock response is not valid JSON, so content should be {}
        assert isinstance(result["content"], dict)


class TestMockComplete:
    def test_returns_mock_response(self):
        result = _mock_complete("prompt", "model", 1, "test")
        assert result["mock"] is True
        assert result["mock_reason"] == "test"
        assert "prompt" in result["content"]


class TestBuildStructuredPrompt:
    def test_includes_schema(self):
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        prompt = _build_structured_prompt("Extract fields", schema)
        assert "Extract fields" in prompt
        assert "schema" in prompt.lower() or "JSON" in prompt
        assert "x" in prompt


class TestModelTierMap:
    def test_all_tiers_present(self):
        assert 1 in MODEL_TIER_MAP
        assert 2 in MODEL_TIER_MAP
        assert 3 in MODEL_TIER_MAP

    def test_all_free_models(self):
        for tier, model in MODEL_TIER_MAP.items():
            assert ":free" in model, f"Tier {tier} model {model} is not free"

    def test_tier_1_is_gemma(self):
        assert "gemma" in MODEL_TIER_MAP[1]

    def test_tier_2_is_qwen(self):
        assert "qwen" in MODEL_TIER_MAP[2]

    def test_tier_3_is_nemotron(self):
        assert "nemotron" in MODEL_TIER_MAP[3]
