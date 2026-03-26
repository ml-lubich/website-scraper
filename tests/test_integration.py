"""Real integration tests that actually import and test the code."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

# Import the actual modules - no mocks!
from website_scraper import WebScraper, ScraperConfig
from website_scraper.browser import PlaywrightDriver, PlaywrightConfig, StealthConfig
from website_scraper.extractors import ContentExtractor, LinkExtractor
from website_scraper.exporters import (
    JSONExporter,
    MarkdownExporter,
    CSVExporter,
    create_exporter,
    ScrapingResult,
    ScrapingStats,
)
from website_scraper.llm import create_llm_provider, LLMProviderType


class TestContentExtractorIntegration:
    """Real tests for ContentExtractor that actually use it."""
    
    def test_extract_real_html(self):
        """Test extracting content from real HTML."""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Test Page</title>
            <meta name="description" content="A test page">
            <meta name="author" content="Test Author">
        </head>
        <body>
            <h1>Main Heading</h1>
            <p>This is a paragraph with content.</p>
            <h2>Sub Heading</h2>
            <p>Another paragraph here.</p>
            <a href="/page1">Link 1</a>
            <a href="https://external.com">External</a>
            <img src="/image.jpg" alt="Test image">
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Verify actual extraction
        assert result.title == "Test Page"
        assert "Main Heading" in result.text
        assert result.meta_description == "A test page"
        assert result.author == "Test Author"
        assert len(result.headings) > 0
        assert len(result.internal_links) > 0
        assert len(result.external_links) > 0
        assert len(result.images) > 0
    
    def test_extract_minimal_html(self):
        """Test extraction from minimal HTML."""
        html = "<html><head><title>Minimal</title></head><body><p>Content</p></body></html>"
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        assert result.title == "Minimal"
        assert "Content" in result.text
    
    def test_extract_no_images_when_disabled(self):
        """Test image extraction can be disabled."""
        html = '<html><body><img src="/test.jpg" alt="Test"></body></html>'
        
        extractor = ContentExtractor(extract_images=False)
        result = extractor.extract(html, "https://example.com")
        
        assert len(result.images) == 0
    
    def test_extract_links_separation(self):
        """Test internal vs external link separation."""
        html = """
        <html>
        <body>
            <a href="/internal">Internal</a>
            <a href="https://external.com/page">External</a>
            <a href="https://example.com/page">Same Domain</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Should have internal links
        assert len(result.internal_links) >= 1
        # Should have external links
        assert any("external.com" in link for link in result.external_links)


class TestLinkExtractorIntegration:
    """Real tests for LinkExtractor that actually use it."""
    
    def test_extract_links_from_html(self):
        """Test extracting links from HTML."""
        html = """
        <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="https://external.com">External</a>
        </body>
        </html>
        """
        
        extractor = LinkExtractor("https://example.com")
        links = extractor.extract(html)
        
        assert len(links) >= 2
        urls = [link.url for link in links]
        assert any("/page1" in url or "page1" in url for url in urls)
    
    def test_classify_navigation_links(self):
        """Test navigation link classification."""
        html = """
        <html>
        <body>
            <a href="/login">Login</a>
            <a href="/article">Article</a>
        </body>
        </html>
        """
        
        extractor = LinkExtractor("https://example.com")
        links = extractor.extract(html)
        
        nav_links = [l for l in links if l.is_navigation or l.link_type == "navigation"]
        assert len(nav_links) >= 1


class TestExporterIntegration:
    """Real tests for exporters that actually use them."""
    
    def test_json_exporter_real_export(self, temp_dir):
        """Test JSON exporter with real data."""
        results = [
            ScrapingResult(
                url="https://example.com/page1",
                title="Page 1",
                content="Content here",
            ),
            ScrapingResult(
                url="https://example.com/page2",
                title="Page 2",
                content="More content",
            ),
        ]
        
        exporter = JSONExporter()
        output = asyncio.run(exporter.export(results))
        
        # Verify it's valid JSON
        import json
        data = json.loads(output)
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["url"] == "https://example.com/page1"
    
    def test_markdown_exporter_real_export(self, temp_dir):
        """Test Markdown exporter with real data."""
        results = [
            ScrapingResult(
                url="https://example.com/page",
                title="Test Page",
                content="This is the content.",
            ),
        ]
        
        exporter = MarkdownExporter()
        output = asyncio.run(exporter.export(results))
        
        # Verify markdown structure
        assert "# Web Scraping Results" in output
        assert "Test Page" in output
        assert "This is the content" in output
    
    def test_csv_exporter_real_export(self, temp_dir):
        """Test CSV exporter with real data."""
        results = [
            ScrapingResult(
                url="https://example.com/page",
                title="Test Page",
                content="Content here",
            ),
        ]
        
        exporter = CSVExporter()
        output = asyncio.run(exporter.export(results))
        
        # Verify CSV structure
        assert "url" in output
        assert "title" in output
        assert "https://example.com/page" in output
        assert "Test Page" in output
    
    def test_exporter_factory(self):
        """Test exporter factory creates correct types."""
        json_exporter = create_exporter("json")
        assert isinstance(json_exporter, JSONExporter)
        
        markdown_exporter = create_exporter("markdown")
        assert isinstance(markdown_exporter, MarkdownExporter)
        
        csv_exporter = create_exporter("csv")
        assert isinstance(csv_exporter, CSVExporter)


class TestScraperIntegration:
    """Real integration tests for the scraper."""
    
    def test_scraper_initialization(self, temp_dir):
        """Test scraper can be initialized."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
            log_dir=str(temp_dir),
        )
        
        scraper = WebScraper(config=config)
        
        assert scraper.base_url == "https://example.com"
        assert scraper.config.max_pages == 1
    
    def test_scraper_config_defaults(self):
        """Test scraper config has correct defaults."""
        config = ScraperConfig()
        
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.llm_provider == "off"
        assert config.output_format == "json"
    
    @pytest.mark.asyncio
    async def test_scraper_context_manager(self, temp_dir):
        """Test scraper can be used as async context manager."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
            log_dir=str(temp_dir),
            headless=True,
        )
        
        # This should not raise
        async with WebScraper(config=config) as scraper:
            assert scraper._driver is not None
            assert scraper._driver.is_running is True


class TestBrowserIntegration:
    """Real tests for browser module."""
    
    @pytest.mark.asyncio
    async def test_playwright_driver_initialization(self):
        """Test Playwright driver can be initialized."""
        config = PlaywrightConfig(
            browser_type="chromium",
            headless=True,
        )
        
        driver = PlaywrightDriver(config)
        
        # Should be able to start
        await driver.start()
        assert driver.is_running is True
        
        # Should be able to create a page
        page = await driver.new_page()
        assert page is not None
        
        # Cleanup
        await page.close()
        await driver.close()
    
    @pytest.mark.asyncio
    async def test_stealth_config(self):
        """Test stealth configuration."""
        config = StealthConfig(
            min_delay=2.0,
            max_delay=5.0,
        )
        
        assert config.min_delay == 2.0
        assert config.max_delay == 5.0
        
        # Test random delay is in range
        delay = config.get_random_delay()
        assert 2.0 <= delay <= 5.0
    
    @pytest.mark.asyncio
    async def test_playwright_driver_context_manager(self):
        """Test Playwright driver as context manager."""
        async with PlaywrightDriver() as driver:
            assert driver.is_running is True
            page = await driver.new_page()
            assert page is not None
            await page.close()


class TestLLMFactoryIntegration:
    """Real tests for LLM factory."""
    
    def test_create_off_provider(self):
        """Test creating OFF provider returns None."""
        provider = create_llm_provider("off")
        assert provider is None
    
    def test_create_with_invalid_type_raises(self):
        """Test invalid provider type raises error."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider("invalid_provider")
    
    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        provider = create_llm_provider("ollama")
        assert provider is not None
        assert provider.provider_name == "ollama"
    
    def test_provider_type_from_string(self):
        """Test provider type conversion."""
        from website_scraper.llm.factory import LLMProviderType
        
        assert LLMProviderType.from_string("openai") == LLMProviderType.OPENAI
        assert LLMProviderType.from_string("gpt") == LLMProviderType.OPENAI
        assert LLMProviderType.from_string("anthropic") == LLMProviderType.ANTHROPIC
        assert LLMProviderType.from_string("claude") == LLMProviderType.ANTHROPIC
        assert LLMProviderType.from_string("gemini") == LLMProviderType.GEMINI
        assert LLMProviderType.from_string("ollama") == LLMProviderType.OLLAMA


class TestScrapingResultIntegration:
    """Real tests for ScrapingResult."""
    
    def test_scraping_result_creation(self):
        """Test creating a ScrapingResult."""
        result = ScrapingResult(
            url="https://example.com",
            title="Test",
            content="Content",
        )
        
        assert result.url == "https://example.com"
        assert result.title == "Test"
        assert result.content == "Content"
    
    def test_scraping_result_to_dict(self):
        """Test ScrapingResult to_dict conversion."""
        result = ScrapingResult(
            url="https://example.com",
            title="Test",
            content="Content",
            topics=["topic1", "topic2"],
        )
        
        data = result.to_dict()
        assert data["url"] == "https://example.com"
        assert data["topics"] == ["topic1", "topic2"]


class TestScrapingStatsIntegration:
    """Real tests for ScrapingStats."""
    
    def test_scraping_stats_creation(self):
        """Test creating ScrapingStats."""
        stats = ScrapingStats(
            total_pages=10,
            successful_pages=9,
            failed_pages=1,
            start_url="https://example.com",
        )
        
        assert stats.total_pages == 10
        assert stats.successful_pages == 9
        assert stats.failed_pages == 1
    
    def test_scraping_stats_to_dict(self):
        """Test ScrapingStats to_dict conversion."""
        stats = ScrapingStats(
            total_pages=10,
            successful_pages=9,
            duration_seconds=120,
        )
        
        data = stats.to_dict()
        assert data["total_pages"] == 10
        assert data["successful_pages"] == 9
        assert "success_rate" in data
        assert "duration_formatted" in data


@pytest.mark.slow
class TestPlaywrightRealBrowser:
    """Real tests that use actual Playwright browser."""
    
    @pytest.mark.asyncio
    async def test_playwright_navigate_to_page(self):
        """Test navigating to a real page with Playwright."""
        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            
            # Navigate to a simple test page
            response = await driver.goto(
                page,
                "data:text/html,<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>",
                wait_for="load",
                simulate_human=False,
                handle_cloudflare=False,
            )
            
            assert response is not None
            
            # Get content
            content = await driver.get_page_content(page)
            assert "Hello" in content
            
            # Get title
            title = await driver.get_title(page)
            assert "Test" in title
            
            await page.close()
    
    @pytest.mark.asyncio
    async def test_playwright_extract_links(self):
        """Test extracting links from a page."""
        html = """
        <html>
        <body>
            <a href="/page1">Link 1</a>
            <a href="/page2">Link 2</a>
        </body>
        </html>
        """
        
        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            
            # Navigate to data URL
            await driver.goto(
                page,
                f"data:text/html,{html}",
                simulate_human=False,
            )
            
            # Extract links
            links = await driver.extract_links(page, same_domain=True)
            
            assert len(links) >= 2
            urls = [link["href"] for link in links]
            assert any("page1" in url for url in urls)
            
            await page.close()

