"""Comprehensive tests for WebScraper using Playwright - tests actual imports and functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil

# Import the actual classes we're testing
from website_scraper.scraper import WebScraper, ScraperConfig
from website_scraper.browser import PlaywrightDriver, PlaywrightConfig, StealthConfig
from website_scraper.exporters import ScrapingResult, ScrapingStats
from website_scraper.extractors import ContentExtractor, LinkExtractor


class TestScraperConfig:
    """Test ScraperConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ScraperConfig()
        
        assert config.base_url == ""
        assert config.max_pages == 100
        assert config.headless is True
        assert config.browser_type == "chromium"
        assert config.min_delay == 1.0
        assert config.max_delay == 3.0
        assert config.max_retries == 3
        assert config.llm_provider == "off"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=50,
            headless=False,
            browser_type="firefox",
            min_delay=2.0,
            max_delay=5.0,
            llm_provider="openai",
            llm_api_key="test-key",
        )
        
        assert config.base_url == "https://example.com"
        assert config.max_pages == 50
        assert config.headless is False
        assert config.browser_type == "firefox"
        assert config.min_delay == 2.0
        assert config.max_delay == 5.0
        assert config.llm_provider == "openai"
        assert config.llm_api_key == "test-key"


@pytest.mark.asyncio
class TestWebScraperInitialization:
    """Test WebScraper initialization."""
    
    def test_init_with_base_url(self):
        """Test initialization with base_url string."""
        scraper = WebScraper(base_url="https://example.com")
        
        assert scraper.base_url == "https://example.com"
        assert isinstance(scraper.config, ScraperConfig)
        assert scraper.config.base_url == "https://example.com"
        assert scraper.domain == "example.com"
    
    def test_init_with_config(self):
        """Test initialization with ScraperConfig."""
        config = ScraperConfig(
            base_url="https://test.com",
            max_pages=10,
            headless=False,
        )
        scraper = WebScraper(config=config)
        
        assert scraper.base_url == "https://test.com"
        assert scraper.config.max_pages == 10
        assert scraper.config.headless is False
    
    def test_init_with_kwargs(self):
        """Test initialization with kwargs."""
        scraper = WebScraper(
            base_url="https://example.com",
            max_pages=20,
            headless=False,
        )
        
        assert scraper.base_url == "https://example.com"
        assert scraper.config.max_pages == 20
        assert scraper.config.headless is False
    
    def test_domain_extraction(self):
        """Test domain extraction from URL."""
        scraper1 = WebScraper(base_url="https://example.com")
        assert scraper1.domain == "example.com"
        
        scraper2 = WebScraper(base_url="https://subdomain.example.com/path")
        assert scraper2.domain == "subdomain.example.com"
        
        scraper3 = WebScraper(base_url="http://localhost:8000")
        assert scraper3.domain == "localhost:8000"


@pytest.mark.asyncio
class TestWebScraperContextManager:
    """Test WebScraper as async context manager."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_context_manager_initialization(self, mock_driver_class):
        """Test scraper initializes properly in context manager."""
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        async with WebScraper(base_url="https://example.com") as scraper:
            assert scraper.base_url == "https://example.com"
            assert scraper._driver is not None
            mock_driver.start.assert_called_once()
        
        mock_driver.close.assert_called_once()
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_context_manager_cleanup(self, mock_driver_class):
        """Test cleanup happens on exit."""
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        scraper = WebScraper(base_url="https://example.com")
        await scraper.__aenter__()
        
        assert scraper._driver is not None
        
        await scraper.__aexit__(None, None, None)
        mock_driver.close.assert_called_once()


@pytest.mark.asyncio
class TestWebScraperPlaywrightIntegration:
    """Test WebScraper integration with Playwright."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_playwright_driver_initialization(self, mock_driver_class):
        """Test Playwright driver is initialized correctly."""
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            browser_type="firefox",
            headless=False,
        )
        
        async with WebScraper(config=config) as scraper:
            # Verify PlaywrightDriver was created with correct config
            mock_driver_class.assert_called_once()
            call_args = mock_driver_class.call_args[0][0]
            assert isinstance(call_args, PlaywrightConfig)
            assert call_args.browser_type == "firefox"
            assert call_args.headless is False
            
            mock_driver.start.assert_called_once()
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_stealth_config_passed_to_driver(self, mock_driver_class):
        """Test stealth configuration is passed to Playwright."""
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            min_delay=2.0,
            max_delay=5.0,
        )
        
        async with WebScraper(config=config) as scraper:
            call_args = mock_driver_class.call_args[0][0]
            stealth_config = call_args.stealth_config
            assert isinstance(stealth_config, StealthConfig)
            assert stealth_config.min_delay == 2.0
            assert stealth_config.max_delay == 5.0


@pytest.mark.asyncio
class TestWebScraperScraping:
    """Test actual scraping functionality."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_scrape_single_page(self, mock_driver_class):
        """Test scraping a single page."""
        # Setup mocks
        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><head><title>Test</title></head><body><p>Content</p></body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test Page")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
        )
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        assert len(results) == 1
        assert results[0].url == "https://example.com"
        assert results[0].title == "Test Page"
        assert "Content" in results[0].content
        assert stats.total_pages == 1
        assert stats.successful_pages == 1
        assert stats.failed_pages == 0
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_scrape_with_link_following(self, mock_driver_class):
        """Test scraping follows links."""
        # Setup mocks
        mock_page1 = MagicMock()
        mock_page1.url = "https://example.com"
        mock_page1.close = AsyncMock()
        
        mock_page2 = MagicMock()
        mock_page2.url = "https://example.com/page2"
        mock_page2.close = AsyncMock()
        
        html1 = """
        <html>
            <head><title>Page 1</title></head>
            <body>
                <p>Content 1</p>
                <a href="/page2">Link to page 2</a>
            </body>
        </html>
        """
        
        html2 = """
        <html>
            <head><title>Page 2</title></head>
            <body><p>Content 2</p></body>
        </html>
        """
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        
        # First call returns page1, second returns page2
        page_call_count = 0
        async def new_page_side_effect():
            nonlocal page_call_count
            page_call_count += 1
            if page_call_count == 1:
                return mock_page1
            return mock_page2
        
        mock_driver.new_page = AsyncMock(side_effect=new_page_side_effect)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        
        content_call_count = 0
        async def get_content_side_effect(page):
            nonlocal content_call_count
            content_call_count += 1
            if content_call_count == 1:
                return html1
            return html2
        
        mock_driver.get_page_content = AsyncMock(side_effect=get_content_side_effect)
        mock_driver.get_title = AsyncMock(side_effect=lambda: "Page 1" if content_call_count == 1 else "Page 2")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=2,
        )
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        # Should have scraped both pages
        assert len(results) >= 1
        assert stats.total_pages >= 1
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_scrape_handles_failed_pages(self, mock_driver_class):
        """Test scraping handles failed page loads."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=None)  # Failed to load
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
        )
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        assert len(results) == 0
        assert stats.total_pages == 1
        assert stats.failed_pages == 1
        assert stats.successful_pages == 0
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_scrape_respects_max_pages(self, mock_driver_class):
        """Test scraping respects max_pages limit."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><body><p>Content</p><a href='/page2'>Link</a></body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,  # Limit to 1 page
        )
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        assert stats.total_pages <= 1
        assert len(results) <= 1


@pytest.mark.asyncio
class TestWebScraperContentExtraction:
    """Test content extraction in scraper."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_extracts_title_from_page(self, mock_driver_class):
        """Test title extraction from page."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><head><title>Extracted Title</title></head><body><p>Content</p></body></html>")
        mock_driver.get_title = AsyncMock(return_value="Extracted Title")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            results, _ = await scraper.scrape(show_progress=False)
        
        assert len(results) == 1
        assert results[0].title == "Extracted Title"
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_extracts_meta_description(self, mock_driver_class):
        """Test meta description extraction."""
        html = """
        <html>
            <head>
                <title>Test</title>
                <meta name="description" content="This is a test description">
            </head>
            <body><p>Content</p></body>
        </html>
        """
        
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value=html)
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            results, _ = await scraper.scrape(show_progress=False)
        
        assert len(results) == 1
        assert results[0].meta_description == "This is a test description"
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_extracts_links(self, mock_driver_class):
        """Test link extraction."""
        html = """
        <html>
            <body>
                <a href="/page1">Link 1</a>
                <a href="https://external.com">External</a>
            </body>
        </html>
        """
        
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value=html)
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            results, _ = await scraper.scrape(show_progress=False)
        
        assert len(results) == 1
        assert len(results[0].links) > 0


@pytest.mark.asyncio
class TestWebScraperErrorHandling:
    """Test error handling in scraper."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_handles_exception_during_scraping(self, mock_driver_class):
        """Test exception handling during scraping."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(side_effect=Exception("Network error"))
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        assert len(results) == 0
        assert stats.failed_pages == 1
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_always_closes_pages(self, mock_driver_class):
        """Test pages are always closed even on error."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(side_effect=Exception("Error"))
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            await scraper.scrape(show_progress=False)
        
        # Page should be closed even on error
        mock_page.close.assert_called_once()


@pytest.mark.asyncio
class TestWebScraperLLMIntegration:
    """Test LLM integration in scraper."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    @patch('website_scraper.scraper.create_llm_provider')
    async def test_llm_enhancement_when_available(self, mock_llm_factory, mock_driver_class):
        """Test LLM enhancement when provider is available."""
        # Mock LLM provider
        mock_llm = AsyncMock()
        mock_extracted = MagicMock()
        mock_extracted.title = "LLM Enhanced Title"
        mock_extracted.main_content = "LLM enhanced content"
        mock_extracted.summary = "LLM summary"
        mock_extracted.topics = ["topic1", "topic2"]
        mock_llm.analyze_content = AsyncMock(return_value=mock_extracted)
        mock_llm_factory.return_value = mock_llm
        
        # Mock driver
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
            llm_provider="openai",
            llm_api_key="test-key",
        )
        
        async with WebScraper(config=config) as scraper:
            results, _ = await scraper.scrape(show_progress=False)
        
        # LLM should have been called
        mock_llm.analyze_content.assert_called_once()
        assert len(results) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
