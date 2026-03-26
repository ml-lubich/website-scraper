"""Tests for Playwright driver."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from website_scraper.browser.playwright_driver import (
    PlaywrightDriver,
    PlaywrightConfig,
    create_page,
)
from website_scraper.browser.stealth import StealthConfig


class TestPlaywrightConfig:
    """Tests for PlaywrightConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PlaywrightConfig()
        
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.default_timeout == 30000
        assert config.navigation_timeout == 60000
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PlaywrightConfig(
            browser_type="firefox",
            headless=False,
            default_timeout=60000,
            max_retries=5,
        )
        
        assert config.browser_type == "firefox"
        assert config.headless is False
        assert config.default_timeout == 60000
        assert config.max_retries == 5
    
    def test_stealth_config_integration(self):
        """Test stealth config is properly included."""
        stealth = StealthConfig(min_delay=2.0, max_delay=5.0)
        config = PlaywrightConfig(stealth_config=stealth)
        
        assert config.stealth_config.min_delay == 2.0
        assert config.stealth_config.max_delay == 5.0


class TestPlaywrightDriverInit:
    """Tests for PlaywrightDriver initialization."""
    
    def test_default_init(self):
        """Test default initialization."""
        driver = PlaywrightDriver()
        
        assert driver.config is not None
        assert driver.config.browser_type == "chromium"
        assert driver._browser is None
        assert driver._context is None
    
    def test_custom_config_init(self):
        """Test initialization with custom config."""
        config = PlaywrightConfig(
            browser_type="firefox",
            headless=False,
        )
        driver = PlaywrightDriver(config)
        
        assert driver.config.browser_type == "firefox"
        assert driver.config.headless is False
    
    def test_is_running_before_start(self):
        """Test is_running returns False before start."""
        driver = PlaywrightDriver()
        
        assert driver.is_running is False


@pytest.mark.asyncio
class TestPlaywrightDriverAsync:
    """Async tests for PlaywrightDriver."""
    
    async def test_start_and_close(self, mock_browser, mock_context):
        """Test start and close lifecycle."""
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright = MagicMock()
            mock_playwright.start = AsyncMock(return_value=mock_playwright)
            mock_playwright.stop = AsyncMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            driver = PlaywrightDriver()
            await driver.start()
            
            # Verify browser was launched
            mock_playwright.chromium.launch.assert_called_once()
            
            # Close should cleanup
            await driver.close()
    
    async def test_new_page(self, mock_page, mock_browser, mock_context):
        """Test creating a new page."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        driver._pages = []
        
        page = await driver.new_page()
        
        mock_context.new_page.assert_called_once()
        assert page in driver._pages
    
    async def test_new_page_without_start_raises(self):
        """Test new_page raises error if not started."""
        driver = PlaywrightDriver()
        
        with pytest.raises(RuntimeError, match="Browser not started"):
            await driver.new_page()
    
    async def test_get_page_content(self, mock_page, mock_browser, mock_context):
        """Test getting page content."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.content = AsyncMock(return_value="<html>Test</html>")
        
        content = await driver.get_page_content(mock_page)
        
        assert content == "<html>Test</html>"
        mock_page.content.assert_called_once()
    
    async def test_get_title(self, mock_page, mock_browser, mock_context):
        """Test getting page title."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.title = AsyncMock(return_value="Test Title")
        
        title = await driver.get_title(mock_page)
        
        assert title == "Test Title"
    
    async def test_extract_links(self, mock_page, mock_browser, mock_context):
        """Test link extraction."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.url = "https://example.com"
        mock_page.evaluate = AsyncMock(return_value=[
            {"href": "https://example.com/page1", "text": "Link 1", "is_internal": True},
            {"href": "https://example.com/page2", "text": "Link 2", "is_internal": True},
        ])
        
        links = await driver.extract_links(mock_page)
        
        assert len(links) == 2
        assert links[0]["href"] == "https://example.com/page1"
    
    async def test_take_screenshot(self, mock_page, mock_browser, mock_context, temp_dir):
        """Test taking screenshot."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        
        screenshot = await driver.take_screenshot(mock_page)
        
        assert screenshot == b"fake_screenshot"
    
    async def test_wait_for_selector_success(self, mock_page, mock_browser, mock_context):
        """Test successful selector wait."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.wait_for_selector = AsyncMock()
        
        result = await driver.wait_for_selector(mock_page, "div.content")
        
        assert result is True
    
    async def test_wait_for_selector_timeout(self, mock_page, mock_browser, mock_context):
        """Test selector wait timeout."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))
        
        result = await driver.wait_for_selector(mock_page, "div.missing")
        
        assert result is False
    
    async def test_execute_script(self, mock_page, mock_browser, mock_context):
        """Test JavaScript execution."""
        driver = PlaywrightDriver()
        driver._context = mock_context
        driver._browser = mock_browser
        driver._playwright = MagicMock()
        
        mock_page.evaluate = AsyncMock(return_value="script_result")
        
        result = await driver.execute_script(mock_page, "return 'test'")
        
        assert result == "script_result"


@pytest.mark.asyncio
class TestCreatePageContextManager:
    """Tests for create_page context manager."""
    
    async def test_create_page_yields_driver_and_page(self, mock_page, mock_browser, mock_context):
        """Test context manager yields driver and page."""
        with patch('website_scraper.browser.playwright_driver.async_playwright') as mock_pw:
            mock_playwright = MagicMock()
            mock_playwright.start = AsyncMock(return_value=mock_playwright)
            mock_playwright.stop = AsyncMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_browser.close = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_context.close = AsyncMock()
            mock_page.close = AsyncMock()
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)
            
            async with create_page() as (driver, page):
                assert driver is not None
                assert page is not None

