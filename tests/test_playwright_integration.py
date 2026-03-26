"""Integration tests to verify Playwright is actually being used."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from website_scraper import WebScraper, ScraperConfig
from website_scraper.browser import PlaywrightDriver, PlaywrightConfig


def setup_mock_playwright(mock_pw):
    """Helper to setup mock Playwright with all required async methods."""
    mock_playwright = MagicMock()
    mock_playwright.start = AsyncMock(return_value=mock_playwright)
    mock_playwright.stop = AsyncMock()
    mock_playwright.chromium = MagicMock()
    mock_playwright.firefox = MagicMock()
    mock_playwright.webkit = MagicMock()
    
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    # Setup async methods
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_playwright.firefox.launch = AsyncMock(return_value=mock_browser)
    mock_playwright.webkit.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.add_init_script = AsyncMock()  # Critical: must be AsyncMock
    mock_context.set_default_timeout = MagicMock()
    mock_context.set_default_navigation_timeout = MagicMock()
    mock_context.close = AsyncMock()
    mock_browser.close = AsyncMock()
    mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
    mock_page.title = AsyncMock(return_value="Test Page")
    mock_page.close = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    
    # async_playwright() returns an object with .start() method
    mock_pw_instance = MagicMock()
    mock_pw_instance.start = AsyncMock(return_value=mock_playwright)
    mock_pw.return_value = mock_pw_instance
    
    return mock_playwright, mock_browser, mock_context, mock_page


@pytest.mark.asyncio
class TestPlaywrightIntegration:
    """Tests to verify Playwright integration works correctly."""
    
    async def test_scraper_uses_playwright_driver(self):
        """Verify that WebScraper actually uses PlaywrightDriver."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
        )
        
        scraper = WebScraper(config=config)
        
        # Before initialization, driver should be None
        assert scraper._driver is None
        
        # Mock Playwright to avoid actual browser launch
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page = setup_mock_playwright(mock_pw)
            mock_response = MagicMock()
            mock_response.status = 200
            
            # Initialize scraper
            await scraper._initialize()
            
            # Verify PlaywrightDriver was created
            assert scraper._driver is not None
            assert isinstance(scraper._driver, PlaywrightDriver)
            
            # Verify Playwright was called
            mock_pw.assert_called()
            # The start() is called on the return value of async_playwright()
            mock_pw.return_value.start.assert_called()
            mock_playwright.chromium.launch.assert_called()
            mock_context.add_init_script.assert_called()  # Verify stealth was applied
            
            # Cleanup
            await scraper._cleanup()
    
    async def test_playwright_driver_initialization(self):
        """Test that PlaywrightDriver initializes correctly."""
        config = PlaywrightConfig(
            browser_type="chromium",
            headless=True,
        )
        
        driver = PlaywrightDriver(config)
        
        assert driver.config == config
        assert driver._browser is None  # Not started yet
        assert driver._context is None
        assert driver.is_running is False
    
    async def test_playwright_driver_start_stop(self):
        """Test PlaywrightDriver start and stop lifecycle."""
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page = setup_mock_playwright(mock_pw)
            
            driver = PlaywrightDriver()
            
            # Start driver
            await driver.start()
            
            assert driver.is_running is True
            assert driver._browser is not None
            assert driver._context is not None
            
            # Verify Playwright was started
            mock_pw.return_value.start.assert_called()  # start() called on async_playwright() result
            mock_playwright.chromium.launch.assert_called()
            mock_context.add_init_script.assert_called()  # Stealth applied
            
            # Stop driver
            await driver.close()
            
            assert driver.is_running is False
            mock_browser.close.assert_called()
            mock_context.close.assert_called()
            mock_playwright.stop.assert_called()
    
    async def test_scraper_process_url_uses_playwright(self):
        """Verify that _process_url uses Playwright to navigate."""
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
        )
        
        scraper = WebScraper(config=config)
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page = setup_mock_playwright(mock_pw)
            mock_response = MagicMock()
            mock_response.status = 200
            
            await scraper._initialize()
            
            # Mock the driver's goto method
            scraper._driver.goto = AsyncMock(return_value=mock_response)
            scraper._driver.get_page_content = AsyncMock(return_value="<html><body>Test</body></html>")
            scraper._driver.get_title = AsyncMock(return_value="Test Page")
            
            # Process a URL
            result = await scraper._process_url("https://example.com/test")
            
            # Verify Playwright methods were called
            scraper._driver.goto.assert_called_once()
            scraper._driver.get_page_content.assert_called_once()
            scraper._driver.get_title.assert_called_once()
            
            # Verify result was created
            assert result is not None
            assert result.url == "https://example.com/test"
            
            await scraper._cleanup()
    
    async def test_playwright_config_passed_to_driver(self):
        """Verify that scraper config is properly passed to PlaywrightDriver."""
        config = ScraperConfig(
            base_url="https://example.com",
            browser_type="firefox",
            headless=False,
            page_timeout=60000,
            navigation_timeout=120000,
        )
        
        scraper = WebScraper(config=config)
        
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page = setup_mock_playwright(mock_pw)
            
            await scraper._initialize()
            
            # Verify Firefox was launched (not Chromium)
            mock_playwright.firefox.launch.assert_called()
            
            # Verify driver config matches scraper config
            assert scraper._driver.config.browser_type == "firefox"
            assert scraper._driver.config.headless is False
            
            await scraper._cleanup()


@pytest.mark.asyncio
class TestPlaywrightRealBehavior:
    """Tests that verify Playwright behavior (with mocks)."""
    
    async def test_goto_with_retry(self):
        """Test that goto retries on failure."""
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page = setup_mock_playwright(mock_pw)
            
            config = PlaywrightConfig(max_retries=3, retry_delay=0.1)
            driver = PlaywrightDriver(config)
            await driver.start()
            
            # Mock goto to fail twice then succeed
            call_count = 0
            async def mock_goto(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    from playwright.async_api import Error as PlaywrightError
                    raise PlaywrightError("Network error")
                return MagicMock(status=200)
            
            mock_page.goto = mock_goto
            
            # Should succeed after retries
            result = await driver.goto(mock_page, "https://example.com")
            
            assert result is not None
            assert call_count == 3  # Should have retried
            
            await driver.close()
    
    async def test_cloudflare_handling(self):
        """Test that Cloudflare challenges are handled."""
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright, mock_browser, mock_context, mock_page = setup_mock_playwright(mock_pw)
            
            driver = PlaywrightDriver()
            await driver.start()
            
            # Mock page content to simulate Cloudflare
            mock_page.content = AsyncMock(return_value="<html><body>Checking your browser...</body></html>")
            mock_page.title = AsyncMock(return_value="Just a moment...")
            mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
            
            # Mock wait_for_cloudflare
            with patch('website_scraper.browser.playwright_driver.wait_for_cloudflare') as mock_wait:
                mock_wait.return_value = True
                
                result = await driver.goto(
                    mock_page,
                    "https://example.com",
                    handle_cloudflare=True,
                )
                
                # Should have called wait_for_cloudflare
                mock_wait.assert_called()
            
            await driver.close()
