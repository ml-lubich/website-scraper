"""Test that all imports work correctly."""

import pytest


def test_main_package_imports():
    """Test that main package imports work."""
    from website_scraper import (
        WebScraper,
        IntelligentScraper,
        ScraperConfig,
        scrape_url,
        PlaywrightDriver,
        PlaywrightConfig,
        StealthConfig,
        BaseLLMProvider,
        LLMConfig,
        LLMProviderType,
        create_llm_provider,
        ExtractedContent,
        ScoredLink,
        ContentExtractor,
        ExtractedPageData,
        LinkExtractor,
        LinkInfo,
        BaseExporter,
        ExportConfig,
        ScrapingResult,
        ScrapingStats,
        JSONExporter,
        MarkdownExporter,
        CSVExporter,
        create_exporter,
        ExporterType,
    )
    
    # Verify classes exist
    assert WebScraper is not None
    assert IntelligentScraper is not None
    assert ScraperConfig is not None
    assert callable(scrape_url)
    assert PlaywrightDriver is not None
    assert ContentExtractor is not None
    assert JSONExporter is not None


def test_browser_module_imports():
    """Test browser module imports."""
    from website_scraper.browser import (
        PlaywrightDriver,
        PlaywrightConfig,
        StealthConfig,
        apply_stealth,
        simulate_human_behavior,
        wait_for_cloudflare,
        get_browser_args,
    )
    
    assert PlaywrightDriver is not None
    assert StealthConfig is not None
    assert callable(apply_stealth)
    assert callable(get_browser_args)


def test_extractors_module_imports():
    """Test extractors module imports."""
    from website_scraper.extractors import (
        ContentExtractor,
        ExtractedPageData,
        LinkExtractor,
        LinkInfo,
    )
    
    assert ContentExtractor is not None
    assert ExtractedPageData is not None
    assert LinkExtractor is not None
    assert LinkInfo is not None


def test_exporters_module_imports():
    """Test exporters module imports."""
    from website_scraper.exporters import (
        BaseExporter,
        ExportConfig,
        ScrapingResult,
        ScrapingStats,
        JSONExporter,
        MarkdownExporter,
        CSVExporter,
        create_exporter,
        ExporterType,
    )
    
    assert BaseExporter is not None
    assert ExportConfig is not None
    assert JSONExporter is not None
    assert callable(create_exporter)


def test_llm_module_imports():
    """Test LLM module imports."""
    from website_scraper.llm import (
        BaseLLMProvider,
        LLMConfig,
        ExtractedContent,
        ScoredLink,
        create_llm_provider,
        LLMProviderType,
    )
    
    assert BaseLLMProvider is not None
    assert LLMConfig is not None
    assert ExtractedContent is not None
    assert callable(create_llm_provider)


def test_version_import():
    """Test version import."""
    from website_scraper import __version__
    
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0
