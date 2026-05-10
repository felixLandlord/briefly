import pytest
from app.core.llm import LLM_OPTIONS


class TestLLMOptions:
    def test_base_model_anthropic(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.base_model == "claude-sonnet-4-6"
        assert LLM_OPTIONS.CLAUDE_HAIKU_4_5.base_model == "claude-haiku-4-5"
        assert LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MAX.base_model == "claude-opus-4-6"

    def test_base_model_openai(self):
        assert LLM_OPTIONS.GPT_5_MINI.base_model == "gpt-5-mini"
        assert LLM_OPTIONS.GPT_5.base_model == "gpt-5"

    def test_base_model_inception(self):
        assert LLM_OPTIONS.MERCURY_2.base_model == "mercury-2"

    def test_base_model_minimax(self):
        assert LLM_OPTIONS.MINIMAX_2_7.base_model == "MiniMax-M2.7"

    def test_is_anthropic(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.is_anthropic is True
        assert LLM_OPTIONS.GPT_5_MINI.is_anthropic is False
        assert LLM_OPTIONS.MINIMAX_2_7.is_anthropic is False

    def test_is_openai(self):
        assert LLM_OPTIONS.GPT_5_MINI.is_openai is True
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.is_openai is False

    def test_is_inception(self):
        assert LLM_OPTIONS.MERCURY_2.is_inception is True
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.is_inception is False

    def test_is_minimax(self):
        assert LLM_OPTIONS.MINIMAX_2_7.is_minimax is True
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.is_minimax is False


class TestThinkingProperty:
    def test_sonnet_4_6_adaptive(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_LOW.thinking == {"type": "adaptive"}
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_MEDIUM.thinking == {"type": "adaptive"}
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_HIGH.thinking == {"type": "adaptive"}

    def test_opus_4_6_thinking_max(self):
        assert LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MAX.thinking == {"type": "adaptive"}

    def test_thinking_low_budget(self):
        assert LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_LOW.thinking == {"type": "enabled", "budget_tokens": 4_000}
        assert LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_LOW.thinking == {"type": "enabled", "budget_tokens": 4_000}

    def test_thinking_medium_budget(self):
        assert LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_MEDIUM.thinking == {"type": "enabled", "budget_tokens": 8_000}

    def test_thinking_high_budget(self):
        assert LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_HIGH.thinking == {"type": "enabled", "budget_tokens": 16_000}

    def test_non_thinking_model_returns_none(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.thinking is None
        assert LLM_OPTIONS.GPT_5_MINI.thinking is None
        assert LLM_OPTIONS.MINIMAX_2_7.thinking is None


class TestEffortProperty:
    def test_opus_4_6_thinking_max_effort(self):
        assert LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MAX.effort == "max"

    def test_thinking_low_effort(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_LOW.effort == "low"
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_LOW.effort == "low"

    def test_thinking_medium_effort(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_MEDIUM.effort == "medium"
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_MEDIUM.effort == "medium"

    def test_thinking_high_effort(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_HIGH.effort == "high"
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_HIGH.effort == "high"

    def test_non_thinking_model_returns_none(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.effort is None
        assert LLM_OPTIONS.GPT_5_MINI.effort is None


class TestReasoningProperty:
    def test_gpt_5_mini_reasoning_low(self):
        assert LLM_OPTIONS.GPT_5_MINI_REASONING_LOW.reasoning == {"effort": "low", "summary": "auto"}

    def test_gpt_5_mini_reasoning_medium(self):
        assert LLM_OPTIONS.GPT_5_MINI_REASONING_MEDIUM.reasoning == {"effort": "medium", "summary": "auto"}

    def test_gpt_5_mini_reasoning_high(self):
        assert LLM_OPTIONS.GPT_5_MINI_REASONING_HIGH.reasoning == {"effort": "high", "summary": "auto"}

    def test_non_reasoning_model_returns_none(self):
        assert LLM_OPTIONS.CLAUDE_SONNET_4_6.reasoning is None
        assert LLM_OPTIONS.MINIMAX_2_7.reasoning is None
