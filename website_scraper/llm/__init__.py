"""LLM integration module for intelligent content extraction and navigation."""

from .base import BaseLLMProvider, ExtractedContent, ScoredLink, LLMConfig, ContentType
from .factory import (
    create_llm_provider,
    LLMProviderType,
    get_available_providers,
    auto_detect_provider,
)
# Provider classes are defined in factory.py but may not be importable if dependencies missing
try:
    from .factory import OpenAIProvider, AnthropicProvider, GeminiProvider
except ImportError:
    OpenAIProvider = None
    AnthropicProvider = None
    GeminiProvider = None

__all__ = [
    "BaseLLMProvider",
    "ExtractedContent",
    "ScoredLink",
    "LLMConfig",
    "ContentType",
    "create_llm_provider",
    "LLMProviderType",
    "get_available_providers",
    "auto_detect_provider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
]
