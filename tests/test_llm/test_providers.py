"""Tests for LLM providers."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json
import os

from website_scraper.llm.base import (
    BaseLLMProvider,
    LLMConfig,
    ExtractedContent,
    ScoredLink,
    ContentType,
)
from website_scraper.llm.factory import (
    create_llm_provider,
    LLMProviderType,
    get_available_providers,
    auto_detect_provider,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LLMConfig()
        
        assert config.api_key is None
        assert config.temperature == 0.1
        assert config.max_tokens == 4096
        assert config.timeout == 60.0
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=8192,
        )
        
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 8192
    
    def test_config_with_base_url(self):
        """Test config with custom base URL."""
        config = LLMConfig(
            api_base_url="http://localhost:8080",
        )
        
        assert config.api_base_url == "http://localhost:8080"


class TestExtractedContent:
    """Tests for ExtractedContent dataclass."""
    
    def test_default_content(self):
        """Test default values."""
        content = ExtractedContent()
        
        assert content.title == ""
        assert content.main_content == ""
        assert content.topics == []
        assert content.confidence_score == 0.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        content = ExtractedContent(
            title="Test Title",
            main_content="Test content",
            summary="Test summary",
            topics=["topic1", "topic2"],
            confidence_score=0.95,
            author="Test Author",
            date_published="2024-01-01",
        )
        
        data = content.to_dict()
        
        assert data["title"] == "Test Title"
        assert data["main_content"] == "Test content"
        assert data["summary"] == "Test summary"
        assert data["topics"] == ["topic1", "topic2"]
        assert data["confidence_score"] == 0.95
        assert data["author"] == "Test Author"
    
    def test_content_with_extraction_notes(self):
        """Test content with extraction notes (for errors)."""
        content = ExtractedContent(extraction_notes="Failed to parse")
        
        assert content.extraction_notes == "Failed to parse"


class TestScoredLink:
    """Tests for ScoredLink dataclass."""
    
    def test_default_link(self):
        """Test default values."""
        link = ScoredLink(url="https://example.com", text="Example")
        
        assert link.url == "https://example.com"
        assert link.text == "Example"
        assert link.relevance_score == 0.0
        assert link.should_follow is True
        assert link.priority == 0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        link = ScoredLink(
            url="https://example.com",
            text="Example",
            relevance_score=0.8,
            priority=2,
            should_follow=True,
            reasoning="High relevance",
            link_type="content",
        )
        
        data = link.to_dict()
        
        assert data["url"] == "https://example.com"
        assert data["text"] == "Example"
        assert data["relevance_score"] == 0.8
        assert data["priority"] == 2
        assert data["should_follow"] is True
        assert data["reasoning"] == "High relevance"


class TestContentType:
    """Tests for ContentType enum."""
    
    def test_content_types_exist(self):
        """Test content types are defined."""
        assert ContentType.MAIN_CONTENT.value == "main_content"
        assert ContentType.NAVIGATION.value == "navigation"
        assert ContentType.ADVERTISEMENT.value == "advertisement"
        assert ContentType.FOOTER.value == "footer"
        assert ContentType.SIDEBAR.value == "sidebar"
        assert ContentType.HEADER.value == "header"
        assert ContentType.UNKNOWN.value == "unknown"


class TestLLMProviderType:
    """Tests for LLMProviderType enum."""
    
    def test_provider_types(self):
        """Test provider types are defined."""
        assert LLMProviderType.OPENAI.value == "openai"
        assert LLMProviderType.ANTHROPIC.value == "anthropic"
        assert LLMProviderType.GEMINI.value == "gemini"
        assert LLMProviderType.OLLAMA.value == "ollama"
    
    def test_from_string_exact(self):
        """Test from_string with exact matches."""
        assert LLMProviderType.from_string("openai") == LLMProviderType.OPENAI
        assert LLMProviderType.from_string("anthropic") == LLMProviderType.ANTHROPIC
        assert LLMProviderType.from_string("gemini") == LLMProviderType.GEMINI
        assert LLMProviderType.from_string("ollama") == LLMProviderType.OLLAMA
    
    def test_from_string_aliases(self):
        """Test from_string with aliases."""
        assert LLMProviderType.from_string("gpt") == LLMProviderType.OPENAI
        assert LLMProviderType.from_string("claude") == LLMProviderType.ANTHROPIC
        assert LLMProviderType.from_string("google") == LLMProviderType.GEMINI
        assert LLMProviderType.from_string("local") == LLMProviderType.OLLAMA
    
    def test_from_string_case_insensitive(self):
        """Test from_string is case insensitive."""
        assert LLMProviderType.from_string("OPENAI") == LLMProviderType.OPENAI
        assert LLMProviderType.from_string("OpenAI") == LLMProviderType.OPENAI
    
    def test_from_string_invalid_raises(self):
        """Test from_string raises for invalid provider."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMProviderType.from_string("invalid_provider")


class TestBaseLLMProvider:
    """Tests for BaseLLMProvider base class."""
    
    def test_truncate_content_short(self):
        """Test that short content is not truncated."""
        config = LLMConfig(max_content_length=100)
        
        class TestProvider(BaseLLMProvider):
            @property
            def provider_name(self):
                return "test"
            
            @property
            def default_model(self):
                return "test-model"
            
            async def analyze_content(self, *args, **kwargs):
                return ExtractedContent()
            
            async def analyze_links(self, *args, **kwargs):
                return []
            
            async def summarize_content(self, *args, **kwargs):
                return ""
        
        provider = TestProvider(config)
        
        short_content = "x" * 50
        result = provider._truncate_content(short_content)
        
        assert result == short_content
    
    def test_truncate_content_long(self):
        """Test that long content is truncated."""
        config = LLMConfig(max_content_length=100)
        
        class TestProvider(BaseLLMProvider):
            @property
            def provider_name(self):
                return "test"
            
            @property
            def default_model(self):
                return "test-model"
            
            async def analyze_content(self, *args, **kwargs):
                return ExtractedContent()
            
            async def analyze_links(self, *args, **kwargs):
                return []
            
            async def summarize_content(self, *args, **kwargs):
                return ""
        
        provider = TestProvider(config)
        
        long_content = "x" * 200
        result = provider._truncate_content(long_content)
        
        assert len(result) <= 100
        assert "[Content truncated...]" in result
    
    def test_content_extraction_prompt(self):
        """Test content extraction prompt generation."""
        class TestProvider(BaseLLMProvider):
            @property
            def provider_name(self):
                return "test"
            
            @property
            def default_model(self):
                return "test-model"
            
            async def analyze_content(self, *args, **kwargs):
                return ExtractedContent()
            
            async def analyze_links(self, *args, **kwargs):
                return []
            
            async def summarize_content(self, *args, **kwargs):
                return ""
        
        provider = TestProvider()
        
        prompt = provider._get_content_extraction_prompt(
            "https://example.com",
            "Find product information"
        )
        
        assert "https://example.com" in prompt
        assert "Find product information" in prompt
        assert "JSON" in prompt
    
    def test_link_analysis_prompt(self):
        """Test link analysis prompt generation."""
        class TestProvider(BaseLLMProvider):
            @property
            def provider_name(self):
                return "test"
            
            @property
            def default_model(self):
                return "test-model"
            
            async def analyze_content(self, *args, **kwargs):
                return ExtractedContent()
            
            async def analyze_links(self, *args, **kwargs):
                return []
            
            async def summarize_content(self, *args, **kwargs):
                return ""
        
        provider = TestProvider()
        
        prompt = provider._get_link_analysis_prompt(
            "Product page context",
            "Find related products"
        )
        
        assert "Product page context" in prompt
        assert "Find related products" in prompt
        assert "relevance" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_is_available_with_key(self):
        """Test is_available returns True with API key."""
        config = LLMConfig(api_key="test-key")
        
        class TestProvider(BaseLLMProvider):
            @property
            def provider_name(self):
                return "test"
            
            @property
            def default_model(self):
                return "test-model"
            
            async def analyze_content(self, *args, **kwargs):
                return ExtractedContent()
            
            async def analyze_links(self, *args, **kwargs):
                return []
            
            async def summarize_content(self, *args, **kwargs):
                return ""
        
        provider = TestProvider(config)
        result = await provider.is_available()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_available_without_key(self):
        """Test is_available returns False without API key."""
        config = LLMConfig(api_key=None)
        
        class TestProvider(BaseLLMProvider):
            @property
            def provider_name(self):
                return "test"  # Not ollama
            
            @property
            def default_model(self):
                return "test-model"
            
            async def analyze_content(self, *args, **kwargs):
                return ExtractedContent()
            
            async def analyze_links(self, *args, **kwargs):
                return []
            
            async def summarize_content(self, *args, **kwargs):
                return ""
        
        provider = TestProvider(config)
        result = await provider.is_available()
        
        assert result is False


class TestLLMFactory:
    """Tests for LLM factory functions."""
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider with config."""
        try:
            config = LLMConfig(api_key="test-key")
            provider = create_llm_provider(LLMProviderType.OPENAI, config)
            
            assert provider is not None
            assert provider.provider_name == "openai"
            assert provider.config.api_key == "test-key"
        except ImportError:
            pytest.skip("OpenAI package not installed")
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider with config."""
        try:
            config = LLMConfig(api_key="test-key")
            provider = create_llm_provider(LLMProviderType.ANTHROPIC, config)
            
            assert provider is not None
            assert provider.provider_name == "anthropic"
        except ImportError:
            pytest.skip("Anthropic package not installed")
    
    def test_create_gemini_provider(self):
        """Test creating Gemini provider with config."""
        try:
            config = LLMConfig(api_key="test-key")
            provider = create_llm_provider(LLMProviderType.GEMINI, config)
            
            assert provider is not None
            assert provider.provider_name == "gemini"
        except ImportError:
            pytest.skip("Gemini package not installed")
    
    def test_create_with_string_type(self):
        """Test creating with string type."""
        try:
            config = LLMConfig(api_key="test-key")
            provider = create_llm_provider("openai", config)
            
            assert provider is not None
            assert provider.provider_name == "openai"
        except ImportError:
            pytest.skip("OpenAI package not installed")
    
    def test_create_with_invalid_type_raises(self):
        """Test invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider("invalid_provider")
    
    def test_create_with_custom_model(self):
        """Test creating with custom model."""
        try:
            config = LLMConfig(api_key="test-key", model="gpt-4")
            provider = create_llm_provider(LLMProviderType.OPENAI, config)
            
            assert provider.config.model == "gpt-4"
        except ImportError:
            pytest.skip("OpenAI package not installed")
    
    @pytest.mark.asyncio
    async def test_get_available_providers(self):
        """Test availability map for each provider."""
        providers = await get_available_providers()

        assert isinstance(providers, dict)
        assert "openai" in providers
        assert "anthropic" in providers
        assert "gemini" in providers
        assert "ollama" in providers
        for _name, ok in providers.items():
            assert isinstance(ok, bool)
    
    def test_auto_detect_provider_openai(self):
        """Test auto detection with OpenAI key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            result = auto_detect_provider()
            assert result == LLMProviderType.OPENAI
    
    def test_auto_detect_provider_anthropic(self):
        """Test auto detection with Anthropic key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            result = auto_detect_provider()
            assert result == LLMProviderType.ANTHROPIC
    
    def test_auto_detect_provider_gemini(self):
        """Test auto detection with Google key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True):
            result = auto_detect_provider()
            assert result == LLMProviderType.GEMINI
    
    def test_auto_detect_provider_none(self):
        """Test auto detection with no keys."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing keys
            for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
                os.environ.pop(key, None)
            result = auto_detect_provider()
            assert result is None


class TestProviderInitialization:
    """Tests for provider initialization without requiring packages."""
    
    def test_openai_provider_init_stores_config(self):
        """Test OpenAI provider stores config."""
        # Import at runtime to handle missing packages
        try:
            from website_scraper.llm.openai_provider import OpenAIProvider
            config = LLMConfig(api_key="test", model="gpt-4")
            provider = OpenAIProvider(config)
            
            assert provider.config.api_key == "test"
            assert provider.config.model == "gpt-4"
            assert provider.provider_name == "openai"
            assert provider.default_model == "gpt-4o-mini"
        except ImportError:
            pytest.skip("OpenAI package not installed")
    
    def test_anthropic_provider_init_stores_config(self):
        """Test Anthropic provider stores config."""
        try:
            from website_scraper.llm.anthropic_provider import AnthropicProvider
            config = LLMConfig(api_key="test")
            provider = AnthropicProvider(config)
            
            assert provider.config.api_key == "test"
            assert provider.provider_name == "anthropic"
            assert "claude" in provider.default_model
        except ImportError:
            pytest.skip("Anthropic package not installed")
    
    def test_gemini_provider_init_stores_config(self):
        """Test Gemini provider stores config."""
        try:
            from website_scraper.llm.gemini_provider import GeminiProvider
            config = LLMConfig(api_key="test")
            provider = GeminiProvider(config)
            
            assert provider.config.api_key == "test"
            assert provider.provider_name == "gemini"
            assert "gemini" in provider.default_model
        except ImportError:
            pytest.skip("Gemini package not installed")
    
    def test_ollama_provider_default_config(self):
        """Test Ollama provider uses default config."""
        try:
            from website_scraper.llm.ollama_provider import OllamaProvider
            provider = OllamaProvider()
            
            assert provider.provider_name == "ollama"
            assert provider.config.api_base_url == "http://localhost:11434"
        except ImportError:
            pytest.skip("Ollama provider not available")
