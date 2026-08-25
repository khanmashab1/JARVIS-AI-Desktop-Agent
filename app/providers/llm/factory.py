"""Factory for instantiating LLM providers."""

from app.config import LLMConfig
from app.constants import LLMProviderType
from app.providers.llm.anthropic import AnthropicProvider
from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.ollama import OllamaProvider
from app.providers.llm.openai_compatible import OpenAICompatibleProvider
from app.utils.logging import get_logger

logger = get_logger("providers.llm.factory")


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider based on configuration."""
    provider_type = config.provider.lower()

    if provider_type == LLMProviderType.ANTHROPIC.value:
        logger.info(f"Instantiating Anthropic provider with model: {config.model or 'claude-3-5-sonnet-20241022'}")
        return AnthropicProvider(
            api_key=config.api_key,
            model=config.model or "claude-3-5-sonnet-20241022",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout_seconds=config.timeout_seconds,
            base_url=config.base_url or "https://api.anthropic.com/v1",
        )

    if provider_type == LLMProviderType.OLLAMA.value:
        logger.info(f"Instantiating Ollama provider at {config.base_url or 'http://localhost:11434'} with model {config.model or 'llama3:latest'}")
        return OllamaProvider(
            base_url=config.base_url or "http://localhost:11434",
            model=config.model or "llama3:latest",
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
        )

    if provider_type == LLMProviderType.MOCK.value:
        logger.info("Instantiating Mock LLM provider for testing.")
        return MockLLMProvider()

    # Default to OpenAI-compatible provider
    logger.info(f"Instantiating OpenAI-compatible provider at {config.base_url or 'https://api.openai.com/v1'} with model {config.model or 'gpt-4o'}")
    return OpenAICompatibleProvider(
        base_url=config.base_url or "https://api.openai.com/v1",
        api_key=config.api_key,
        model=config.model or "gpt-4o",
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
    )
