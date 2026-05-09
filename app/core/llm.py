from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from enum import Enum
from typing import Literal, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


_THINKING_LOW = 4_000
_THINKING_MEDIUM = 8_000
_THINKING_HIGH = 16_000

class LLM_OPTIONS(str, Enum):
    # ── Anthropic ────────────────────────────────────────────────
    # Haiku 4.5
    CLAUDE_HAIKU_4_5                      = "claude-haiku-4-5"
    CLAUDE_HAIKU_4_5_THINKING_LOW         = "claude-haiku-4-5:thinking-low"
    CLAUDE_HAIKU_4_5_THINKING_MEDIUM      = "claude-haiku-4-5:thinking-medium"
    CLAUDE_HAIKU_4_5_THINKING_HIGH        = "claude-haiku-4-5:thinking-high"

    # Sonnet 4.5
    CLAUDE_SONNET_4_5                     = "claude-sonnet-4-5"
    CLAUDE_SONNET_4_5_THINKING_LOW        = "claude-sonnet-4-5:thinking-low"
    CLAUDE_SONNET_4_5_THINKING_MEDIUM     = "claude-sonnet-4-5:thinking-medium"
    CLAUDE_SONNET_4_5_THINKING_HIGH       = "claude-sonnet-4-5:thinking-high"

    # Opus 4.5
    CLAUDE_OPUS_4_5                       = "claude-opus-4-5"
    CLAUDE_OPUS_4_5_THINKING_LOW          = "claude-opus-4-5:thinking-low"
    CLAUDE_OPUS_4_5_THINKING_MEDIUM       = "claude-opus-4-5:thinking-medium"
    CLAUDE_OPUS_4_5_THINKING_HIGH         = "claude-opus-4-5:thinking-high"

    # Sonnet 4.6 — adaptive thinking
    CLAUDE_SONNET_4_6                     = "claude-sonnet-4-6"
    CLAUDE_SONNET_4_6_THINKING_LOW        = "claude-sonnet-4-6:thinking-low"
    CLAUDE_SONNET_4_6_THINKING_MEDIUM     = "claude-sonnet-4-6:thinking-medium"
    CLAUDE_SONNET_4_6_THINKING_HIGH       = "claude-sonnet-4-6:thinking-high"

    # Opus 4.6 — adaptive thinking + max effort
    CLAUDE_OPUS_4_6                       = "claude-opus-4-6"
    CLAUDE_OPUS_4_6_THINKING_LOW          = "claude-opus-4-6:thinking-low"
    CLAUDE_OPUS_4_6_THINKING_MEDIUM       = "claude-opus-4-6:thinking-medium"
    CLAUDE_OPUS_4_6_THINKING_HIGH         = "claude-opus-4-6:thinking-high"
    CLAUDE_OPUS_4_6_THINKING_MAX          = "claude-opus-4-6:thinking-max"

    # ── OpenAI ───────────────────────────────────────────────────
    # GPT 5 mini
    GPT_5_MINI                            = "gpt-5-mini"
    GPT_5_MINI_REASONING_LOW              = "gpt-5-mini:reasoning-low"
    GPT_5_MINI_REASONING_MEDIUM           = "gpt-5-mini:reasoning-medium"
    GPT_5_MINI_REASONING_HIGH             = "gpt-5-mini:reasoning-high"

    # GPT 5
    GPT_5                                 = "gpt-5"
    GPT_5_REASONING_LOW                   = "gpt-5:reasoning-low"
    GPT_5_REASONING_MEDIUM                = "gpt-5:reasoning-medium"
    GPT_5_REASONING_HIGH                  = "gpt-5:reasoning-high"

    # GPT 5.1
    GPT_5_1                               = "gpt-5.1"
    GPT_5_1_REASONING_LOW                 = "gpt-5.1:reasoning-low"
    GPT_5_1_REASONING_MEDIUM              = "gpt-5.1:reasoning-medium"
    GPT_5_1_REASONING_HIGH                = "gpt-5.1:reasoning-high"

    # GPT 5.2
    GPT_5_2                               = "gpt-5.2"
    GPT_5_2_REASONING_LOW                 = "gpt-5.2:reasoning-low"
    GPT_5_2_REASONING_MEDIUM              = "gpt-5.2:reasoning-medium"
    GPT_5_2_REASONING_HIGH                = "gpt-5.2:reasoning-high"

    # ── Inception ────────────────────────────────────────────────
    MERCURY_2                             = "mercury-2"
    MERCURY_2_REASONING_INSTANT            = "mercury-2:reasoning-instant"
    MERCURY_2_REASONING_LOW                = "mercury-2:reasoning-low"
    MERCURY_2_REASONING_MEDIUM             = "mercury-2:reasoning-medium"
    MERCURY_2_REASONING_HIGH               = "mercury-2:reasoning-high"

    # ── MiniMax ──────────────────────────────────────────────────
    MINIMAX_2_7 = "MiniMax-2.7"
    MINIMAX_2_5 = "MiniMax-2.5"

    @property
    def base_model(self) -> str:
        """Strip the capability suffix to get the real API model string."""
        return self.value.split(":")[0]

    @property
    def is_anthropic(self) -> bool:
        return self.base_model.startswith("claude")

    @property
    def is_openai(self) -> bool:
        return self.base_model.startswith("gpt")
    
    @property
    def is_inception(self) -> bool:
        return self.base_model.startswith("mercury")
    
    @property
    def is_minimax(self) -> bool:
        return self.base_model.startswith("MiniMax")

    @property
    def thinking(self) -> dict[str, Any] | None:
        match self:
            case (
                LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_LOW
                | LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_MEDIUM
                | LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_HIGH
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_LOW
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MEDIUM
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_HIGH
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MAX
            ):
                return {"type": "adaptive"}
            case (
                LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_LOW 
                | LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_LOW
                | LLM_OPTIONS.CLAUDE_OPUS_4_5_THINKING_LOW
            ):
                return {"type": "enabled", "budget_tokens": _THINKING_LOW}
            case (
                LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_MEDIUM 
                | LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_MEDIUM
                | LLM_OPTIONS.CLAUDE_OPUS_4_5_THINKING_MEDIUM
            ):
                return {"type": "enabled", "budget_tokens": _THINKING_MEDIUM}
            case (
                LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_HIGH 
                | LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_HIGH
                | LLM_OPTIONS.CLAUDE_OPUS_4_5_THINKING_HIGH
            ):
                return {"type": "enabled", "budget_tokens": _THINKING_HIGH}
            case _:
                return None

    @property
    def effort(self) -> Literal["max", "high", "medium", "low"] | None:
        match self:
            case LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MAX:
                return "max"
            case (
                LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_LOW 
                | LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_LOW
                | LLM_OPTIONS.CLAUDE_OPUS_4_5_THINKING_LOW
                | LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_LOW
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_LOW
            ):
                return "low"
            case (
                LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_MEDIUM 
                | LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_MEDIUM
                | LLM_OPTIONS.CLAUDE_OPUS_4_5_THINKING_MEDIUM
                | LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_MEDIUM
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_MEDIUM
            ):
                return "medium"
            case (
                LLM_OPTIONS.CLAUDE_HAIKU_4_5_THINKING_HIGH 
                | LLM_OPTIONS.CLAUDE_SONNET_4_5_THINKING_HIGH
                | LLM_OPTIONS.CLAUDE_OPUS_4_5_THINKING_HIGH
                | LLM_OPTIONS.CLAUDE_SONNET_4_6_THINKING_HIGH
                | LLM_OPTIONS.CLAUDE_OPUS_4_6_THINKING_HIGH
            ):
                return "high"
            case _:
                return None

    @property
    def reasoning(self) -> dict[str, Any] | None:
        match self:
            case (
                LLM_OPTIONS.GPT_5_MINI_REASONING_LOW
                | LLM_OPTIONS.GPT_5_REASONING_LOW
                | LLM_OPTIONS.GPT_5_1_REASONING_LOW
                | LLM_OPTIONS.GPT_5_2_REASONING_LOW
            ):
                return {"effort": "low", "summary": "auto"}
            case (
                LLM_OPTIONS.GPT_5_MINI_REASONING_MEDIUM
                | LLM_OPTIONS.GPT_5_REASONING_MEDIUM
                | LLM_OPTIONS.GPT_5_1_REASONING_MEDIUM
                | LLM_OPTIONS.GPT_5_2_REASONING_MEDIUM
            ):
                return {"effort": "medium", "summary": "auto"}
            case (
                LLM_OPTIONS.GPT_5_MINI_REASONING_HIGH
                | LLM_OPTIONS.GPT_5_REASONING_HIGH
                | LLM_OPTIONS.GPT_5_1_REASONING_HIGH
                | LLM_OPTIONS.GPT_5_2_REASONING_HIGH
            ):
                return {"effort": "high", "summary": "auto"}
            case _:
                return None
    
    @property
    def reasoning_effort(self) -> str | None:
        match self:
            case LLM_OPTIONS.MERCURY_2_REASONING_INSTANT:
                return "instant"
            case LLM_OPTIONS.MERCURY_2_REASONING_LOW:
                return "low"
            case LLM_OPTIONS.MERCURY_2_REASONING_MEDIUM:
                return "medium"
            case LLM_OPTIONS.MERCURY_2_REASONING_HIGH:
                return "high"
            case _:
                return None


class LLM:
    def __init__(
        self,
        temperature: float = 0.0,
        timeout: int = 300,
        max_retries: int = 3,
        max_tokens: int = 64_000,
    ) -> None:
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_tokens = max_tokens

    def get_llm(self, model: LLM_OPTIONS) -> ChatAnthropic | ChatOpenAI:
        """Dispatch to the correct provider method."""
        match model:
            case _ if model.is_anthropic:
                return self._anthropic(model)
            case _ if model.is_openai:
                return self._openai(model)
            case _ if model.is_inception:
                return self._inception(model)
            case _ if model.is_minimax:
                return self._minimax(model)
            case _:
                raise ValueError(f"Unsupported model: {model}")

    def _anthropic(self, model: LLM_OPTIONS) -> ChatAnthropic:
        logger.info("llm.anthropic", model=model, thinking=model.thinking, effort=model.effort)
        return ChatAnthropic(
            model_name=model.base_model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=self.temperature,
            timeout=self.timeout,
            max_retries=self.max_retries,
            max_tokens=self.max_tokens,
            thinking=model.thinking,
            effort=model.effort,
        )

    def _openai(self, model: LLM_OPTIONS) -> ChatOpenAI:
        logger.info("llm.openai", model=model, reasoning=model.reasoning)
        return ChatOpenAI(
            model_name=model.base_model,
            openai_api_key=settings.openai_api_key,
            temperature=self.temperature,
            request_timeout=self.timeout,
            max_retries=self.max_retries,
            max_tokens=self.max_tokens,
            reasoning=model.reasoning,
        )
    
    def _inception(self, model: LLM_OPTIONS) -> ChatOpenAI:
        logger.info("llm.inception", model=model, reasoning=model.reasoning_effort)
        return ChatOpenAI(
            model_name=model.base_model,
            openai_api_key=settings.inception_api_key,
            openai_api_base=settings.inception_api_host,
            temperature=self.temperature,
            request_timeout=self.timeout,
            max_retries=self.max_retries,
            max_tokens=self.max_tokens,
            reasoning_effort=model.reasoning_effort,
        )
    
    def _minimax(self, model: LLM_OPTIONS) -> ChatOpenAI:
        logger.info("llm.minimax", model=model.base_model, temperature=self.temperature)
        return ChatOpenAI(
            model_name=model.base_model,
            openai_api_key=settings.minimax_api_key,
            openai_api_base=settings.minimax_api_host,
            temperature=self.temperature,
            request_timeout=self.timeout,
            max_retries=self.max_retries,
            max_tokens=self.max_tokens,
        )

llm_config = LLM()
