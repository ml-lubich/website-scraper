"""Factory for creating LLM providers."""

import os
import logging
from enum import Enum
from typing import Optional, Union

from .base import BaseLLMProvider, LLMConfig
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM provider types."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OFF = "off"
    
    @classmethod
    def from_string(cls, value: str) -> "LLMProviderType":
        """
        Convert string to LLMProviderType.
        
        Args:
            value: String representation
            
        Returns:
            LLMProviderType enum value
            
        Raises:
            ValueError: If string doesn't match any type
        """
        value = value.lower().strip()
        
        # Handle aliases
        aliases = {
            "gpt": cls.OPENAI,
            "openai": cls.OPENAI,
            "claude": cls.ANTHROPIC,
            "anthropic": cls.ANTHROPIC,
            "google": cls.GEMINI,
            "gemini": cls.GEMINI,
            "ollama": cls.OLLAMA,
            "local": cls.OLLAMA,
            "off": cls.OFF,
            "none": cls.OFF,
        }
        
        if value in aliases:
            return aliases[value]
        
        try:
            return cls(value)
        except ValueError:
            valid = ", ".join([e.value for e in cls])
            raise ValueError(f"Unknown LLM provider: {value}. Valid providers: {valid}")


def create_llm_provider(
    provider_type: Union[str, LLMProviderType],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config: Optional[LLMConfig] = None,
) -> Optional[BaseLLMProvider]:
    """
    Factory function to create an LLM provider instance.
    
    Args:
        provider_type: Type of provider to create (openai, anthropic, gemini, ollama, off)
        api_key: Optional API key (overrides environment variable)
        model: Optional model name
        config: Optional full LLM configuration
        
    Returns:
        Configured LLM provider instance, or None if provider_type is OFF
        
    Raises:
        ValueError: If provider_type is invalid
        ImportError: If required package is not installed
        
    Example:
        >>> provider = create_llm_provider("openai", api_key="sk-...")
        >>> content = await provider.analyze_content(html, url)
    """
    # Convert string to enum if needed
    if isinstance(provider_type, str):
        provider_type = LLMProviderType.from_string(provider_type)
    
    # OFF means no LLM
    if provider_type == LLMProviderType.OFF:
        return None
    
    # Create or update config
    if config is None:
        config = LLMConfig()
    
    # Set API key if provided
    if api_key:
        config.api_key = api_key
    elif not config.api_key:
        # Try environment variables
        env_vars = {
            LLMProviderType.OPENAI: "OPENAI_API_KEY",
            LLMProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProviderType.GEMINI: "GOOGLE_API_KEY",
        }
        env_var = env_vars.get(provider_type)
        if env_var:
            config.api_key = os.environ.get(env_var)
    
    # Set model if provided
    if model:
        config.model = model
    
    # Create appropriate provider
    providers = {
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.GEMINI: GeminiProvider,
        LLMProviderType.OLLAMA: OllamaProvider,
    }
    
    provider_class = providers.get(provider_type)
    if not provider_class:
        raise ValueError(f"No provider registered for type: {provider_type}")
    
    # Validate API key for providers that need it
    if provider_type != LLMProviderType.OLLAMA and not config.api_key:
        env_vars = {
            LLMProviderType.OPENAI: "OPENAI_API_KEY",
            LLMProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProviderType.GEMINI: "GOOGLE_API_KEY",
        }
        env_var = env_vars.get(provider_type)
        raise ValueError(
            f"{provider_type.value} API key not provided. "
            f"Set {env_var} environment variable or pass api_key parameter."
        )
    
    return provider_class(config)


async def get_available_providers() -> dict[str, bool]:
    """
    Check which LLM providers are available.
    
    Returns:
        Dictionary mapping provider names to availability status
    """
    availability = {}
    
    # Check OpenAI
    try:
        provider = create_llm_provider(LLMProviderType.OPENAI, api_key="test")
        availability["openai"] = await provider.is_available() if provider else False
    except (ValueError, ImportError):
        availability["openai"] = False
    
    # Check Anthropic
    try:
        provider = create_llm_provider(LLMProviderType.ANTHROPIC, api_key="test")
        availability["anthropic"] = await provider.is_available() if provider else False
    except (ValueError, ImportError):
        availability["anthropic"] = False
    
    # Check Gemini
    try:
        provider = create_llm_provider(LLMProviderType.GEMINI, api_key="test")
        availability["gemini"] = await provider.is_available() if provider else False
    except (ValueError, ImportError):
        availability["gemini"] = False
    
    # Check Ollama
    try:
        provider = OllamaProvider()
        availability["ollama"] = await provider.is_available()
    except Exception:
        availability["ollama"] = False
    
    return availability


def auto_detect_provider() -> Optional[LLMProviderType]:
    """
    Auto-detect available LLM provider based on environment variables.
    
    Returns:
        Detected provider type or None
    """
    if os.environ.get("OPENAI_API_KEY"):
        return LLMProviderType.OPENAI
    if os.environ.get("ANTHROPIC_API_KEY"):
        return LLMProviderType.ANTHROPIC
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        return LLMProviderType.GEMINI
    return None
