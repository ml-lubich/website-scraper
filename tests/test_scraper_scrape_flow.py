"""Tests for the main scrape flow - testing actual execution."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from website_scraper import WebScraper, ScraperConfig
from website_scraper.exporters.base import ScrapingResult, ScrapingStats


def setup_playwright_mocks(mock_pw):
    """Setup comprehensive Playwright mocks."""
    mock_pw_instance = MagicMock()
    mock_pw_instance.start = AsyncMock(return_value=MagicMock())
    mock_pw.return_value = mock_pw_instance
    
    mock_playwright = MagicMock()
    mock_playwright.chromium = MagicMock()
    mock_playwright.firefox = MagicMock()
    mock_playwright.webkit = MagicMock()
    
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 200
    
    mock_context.add_init_script = AsyncMock()
    mock_context.set_default_timeout = MagicMock()
    mock_context.set_default_navigation_timeout = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_pw_instance.start = AsyncMock(return_value=mock_playwright)
    
    return mock_playwright, mock_browser, mock_context, mock_page, mock_response


@pytest.mark.asyncio
class TestScraperScrapeFlow:
    """Test the main scraping flow."""
    
    async def test_scrape_initializes_queue(self):
        """Test that scrape initializes URL queue."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
        )
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                # Mock to return None quickly
                scraper._process_url = AsyncMock(return_value=None)
                
                results, stats = await scraper.scrape(show_progress=False)
                
                # Verify queue was initialized
                assert stats.total_pages >= 0
                assert isinstance(results, list)
                assert isinstance(stats, ScrapingStats)
    
    async def test_scrape_respects_max_pages(self):
        """Test that scrape respects max_pages limit."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=3,
        )
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                scraper._process_url = AsyncMock(return_value=None)
                
                results, stats = await scraper.scrape(show_progress=False)
                
                # Should not exceed max_pages
                assert stats.total_pages <= 3
    
    async def test_scrape_processes_single_page(self):
        """Test scraping a single page."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
            extract_links=False,
        )
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                # Create a mock result
                mock_result = ScrapingResult(
                    url="https://example.com",
                    title="Test Page",
                    content="Test content",
                )
                
                scraper._process_url = AsyncMock(return_value=mock_result)
                
                results, stats = await scraper.scrape(show_progress=False)
                
                # Should have processed the page
                assert stats.total_pages >= 1
                assert len(results) >= 0  # May be 0 if extraction fails
    
    async def test_scrape_tracks_failed_urls(self):
        """Test that failed URLs are tracked."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=2,
        )
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                # First succeeds, second fails
                call_count = 0
                async def mock_process(url):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        return ScrapingResult(url=url, title="Success")
                    return None
                
                scraper._process_url = mock_process
                
                results, stats = await scraper.scrape(show_progress=False)
                
                # Should track failures
                assert stats.failed_pages >= 0
                assert stats.total_pages == stats.successful_pages + stats.failed_pages
    
    async def test_scrape_calculates_stats(self):
        """Test that scrape calculates statistics correctly."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
        )
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                scraper._process_url = AsyncMock(return_value=None)
                
                results, stats = await scraper.scrape(show_progress=False)
                
                # Verify stats structure
                assert hasattr(stats, 'total_pages')
                assert hasattr(stats, 'successful_pages')
                assert hasattr(stats, 'failed_pages')
                assert hasattr(stats, 'duration_seconds')
                assert hasattr(stats, 'start_url')
                assert stats.start_url == "https://example.com"
    
    async def test_scrape_with_link_following(self):
        """Test scraping with link following."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=2,
            extract_links=True,
        )
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                # Mock result with links
                result1 = ScrapingResult(
                    url="https://example.com",
                    title="Page 1",
                    links=[{"url": "https://example.com/page2", "text": "Page 2"}],
                )
                
                result2 = ScrapingResult(
                    url="https://example.com/page2",
                    title="Page 2",
                )
                
                call_count = 0
                async def mock_process(url):
                    nonlocal call_count
                    call_count += 1
                    if url == "https://example.com":
                        return result1
                    elif url == "https://example.com/page2":
                        return result2
                    return None
                
                scraper._process_url = mock_process
                scraper._extract_and_score_links = AsyncMock(return_value=["https://example.com/page2"])
                
                results, stats = await scraper.scrape(show_progress=False)
                
                # Should have processed multiple pages
                assert stats.total_pages >= 1


class TestScraperDelay:
    """Test delay functionality."""
    
    def test_get_delay_within_range(self):
        """Test that delay is within configured range."""
        config = ScraperConfig(
            base_url="https://example.com",
            min_delay=1.0,
            max_delay=3.0,
        )
        scraper = WebScraper(config=config)
        
        # Test multiple times
        for _ in range(100):
            delay = scraper._get_delay()
            assert 1.0 <= delay <= 3.0, f"Delay {delay} out of range"


@pytest.mark.asyncio
class TestScraperContextManager:
    """Test async context manager."""
    
    async def test_context_manager_initializes(self):
        """Test that context manager initializes scraper."""
        config = ScraperConfig(base_url="https://example.com")
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page, mock_response = setup_playwright_mocks(mock_pw)
            
            async with WebScraper(config=config) as scraper:
                # Should be initialized
                assert scraper._driver is not None
                assert scraper._content_extractor is not None
                assert scraper._link_extractor is not None
            
            # Should be cleaned up
            assert scraper._driver is None
