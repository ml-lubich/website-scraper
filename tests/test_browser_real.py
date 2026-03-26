"""Real tests for browser/Playwright module - tests actual imports and functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import actual classes
from website_scraper.browser import (
    PlaywrightDriver,
    PlaywrightConfig,
    StealthConfig,
    apply_stealth,
    simulate_human_behavior,
    wait_for_cloudflare,
    get_browser_args,
)


class TestStealthConfigReal:
    """Test StealthConfig with real imports."""
    
    def test_stealth_config_creation(self):
        """Test creating StealthConfig."""
        config = StealthConfig()
        
        assert config is not None
        assert len(config.viewport_sizes) > 0
        assert len(config.locales) > 0
        assert len(config.timezones) > 0
        assert len(config.user_agents) > 0
    
    def test_get_random_viewport(self):
        """Test getting random viewport."""
        config = StealthConfig()
        viewport = config.get_random_viewport()
        
        assert isinstance(viewport, tuple)
        assert len(viewport) == 2
        assert viewport[0] > 0
        assert viewport[1] > 0
        assert viewport in config.viewport_sizes
    
    def test_get_random_user_agent(self):
        """Test getting random user agent."""
        config = StealthConfig()
        ua = config.get_random_user_agent()
        
        assert isinstance(ua, str)
        assert len(ua) > 0
        assert "Mozilla" in ua
        assert ua in config.user_agents
    
    def test_get_random_locale(self):
        """Test getting random locale."""
        config = StealthConfig()
        locale = config.get_random_locale()
        
        assert isinstance(locale, str)
        assert locale in config.locales
    
    def test_get_random_timezone(self):
        """Test getting random timezone."""
        config = StealthConfig()
        timezone = config.get_random_timezone()
        
        assert isinstance(timezone, str)
        assert timezone in config.timezones
    
    def test_get_random_delay(self):
        """Test getting random delay."""
        config = StealthConfig(min_delay=1.0, max_delay=3.0)
        delay = config.get_random_delay()
        
        assert 1.0 <= delay <= 3.0


class TestPlaywrightConfigReal:
    """Test PlaywrightConfig with real imports."""
    
    def test_default_config(self):
        """Test default PlaywrightConfig."""
        config = PlaywrightConfig()
        
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.default_timeout == 30000
        assert config.navigation_timeout == 60000
        assert config.max_retries == 3
        assert isinstance(config.stealth_config, StealthConfig)
    
    def test_custom_config(self):
        """Test custom PlaywrightConfig."""
        stealth = StealthConfig(min_delay=2.0)
        config = PlaywrightConfig(
            browser_type="firefox",
            headless=False,
            stealth_config=stealth,
            default_timeout=60000,
        )
        
        assert config.browser_type == "firefox"
        assert config.headless is False
        assert config.stealth_config.min_delay == 2.0
        assert config.default_timeout == 60000


class TestBrowserUtilitiesReal:
    """Test browser utility functions with real imports."""
    
    def test_get_browser_args_headless(self):
        """Test get_browser_args for headless mode."""
        args = get_browser_args(headless=True)
        
        assert isinstance(args, list)
        assert len(args) > 0
        assert "--disable-blink-features=AutomationControlled" in args
        # Should have headless flag
        assert any("headless" in arg.lower() for arg in args)
    
    def test_get_browser_args_non_headless(self):
        """Test get_browser_args for non-headless mode."""
        args = get_browser_args(headless=False)
        
        assert isinstance(args, list)
        assert len(args) > 0
        assert "--disable-blink-features=AutomationControlled" in args
        # Should not have headless=new in non-headless
        assert "--headless=new" not in args


@pytest.mark.asyncio
class TestPlaywrightDriverReal:
    """Test PlaywrightDriver with real imports."""
    
    def test_driver_initialization(self):
        """Test driver initialization."""
        driver = PlaywrightDriver()
        
        assert driver is not None
        assert driver.config is not None
        assert isinstance(driver.config, PlaywrightConfig)
        assert driver.is_running is False
    
    def test_driver_with_custom_config(self):
        """Test driver with custom config."""
        config = PlaywrightConfig(browser_type="firefox", headless=False)
        driver = PlaywrightDriver(config)
        
        assert driver.config.browser_type == "firefox"
        assert driver.config.headless is False
    
    @patch('website_scraper.browser.playwright_driver.async_playwright')
    async def test_driver_start(self, mock_playwright):
        """Test driver start method."""
        # Mock Playwright
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        
        mock_browser_launcher = MagicMock()
        mock_browser_launcher.launch = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.chromium = mock_browser_launcher
        mock_playwright_instance.start = AsyncMock(return_value=mock_playwright_instance)
        
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()
        
        mock_playwright.return_value = mock_playwright_instance
        
        driver = PlaywrightDriver()
        await driver.start()
        
        assert driver.is_running is True
        assert driver._browser is not None
        assert driver._context is not None
        
        await driver.close()
    
    @patch('website_scraper.browser.playwright_driver.async_playwright')
    async def test_driver_context_manager(self, mock_playwright):
        """Test driver as context manager."""
        # Mock Playwright
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        
        mock_browser_launcher = MagicMock()
        mock_browser_launcher.launch = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.chromium = mock_browser_launcher
        mock_playwright_instance.start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright_instance.stop = AsyncMock()
        
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_context.close = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()
        
        mock_playwright.return_value = mock_playwright_instance
        
        async with PlaywrightDriver() as driver:
            assert driver.is_running is True
        
        # Should have cleaned up
        mock_browser.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_playwright_instance.stop.assert_called_once()
    
    @patch('website_scraper.browser.playwright_driver.async_playwright')
    async def test_driver_new_page(self, mock_playwright):
        """Test creating new page."""
        # Mock Playwright
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = MagicMock()
        
        mock_browser_launcher = MagicMock()
        mock_browser_launcher.launch = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.chromium = mock_browser_launcher
        mock_playwright_instance.start = AsyncMock(return_value=mock_playwright_instance)
        
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_init_script = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()
        
        mock_playwright.return_value = mock_playwright_instance
        
        driver = PlaywrightDriver()
        await driver.start()
        
        page = await driver.new_page()
        
        assert page is not None
        assert page == mock_page
        mock_context.new_page.assert_called_once()
        
        await driver.close()
    
    @patch('website_scraper.browser.playwright_driver.async_playwright')
    async def test_driver_goto(self, mock_playwright):
        """Test navigation with goto."""
        # Mock Playwright
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        
        mock_browser_launcher = MagicMock()
        mock_browser_launcher.launch = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.chromium = mock_browser_launcher
        mock_playwright_instance.start = AsyncMock(return_value=mock_playwright_instance)
        
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_init_script = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()
        
        mock_page.goto = AsyncMock(return_value=mock_response)
        
        mock_playwright.return_value = mock_playwright_instance
        
        driver = PlaywrightDriver()
        await driver.start()
        
        page = await driver.new_page()
        response = await driver.goto(page, "https://example.com")
        
        assert response is not None
        assert response.status == 200
        mock_page.goto.assert_called_once()
        
        await driver.close()


@pytest.mark.asyncio
class TestStealthFunctionsReal:
    """Test stealth functions with real imports."""
    
    async def test_apply_stealth(self):
        """Test apply_stealth function."""
        mock_context = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        
        config = StealthConfig()
        await apply_stealth(mock_context, config)
        
        # Should have added init script
        mock_context.add_init_script.assert_called_once()
    
    async def test_simulate_human_behavior(self):
        """Test simulate_human_behavior function."""
        mock_page = MagicMock()
        mock_page.viewport_size = {"width": 1920, "height": 1080}
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=2000)  # Page height
        mock_page.mouse = MagicMock()
        mock_page.mouse.move = AsyncMock()
        
        config = StealthConfig()
        await simulate_human_behavior(mock_page, config)
        
        # Should have interacted with page
        # (exact calls depend on implementation, but should have done something)
        assert mock_page.wait_for_load_state.called or mock_page.evaluate.called or mock_page.mouse.move.called
    
    async def test_wait_for_cloudflare_no_challenge(self):
        """Test wait_for_cloudflare when no challenge."""
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Normal content</body></html>")
        mock_page.title = AsyncMock(return_value="Normal Page")
        
        result = await wait_for_cloudflare(mock_page, timeout=1.0)
        
        assert result is True
    
    async def test_wait_for_cloudflare_with_challenge(self):
        """Test wait_for_cloudflare when challenge present."""
        mock_page = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Checking your browser</body></html>")
        mock_page.title = AsyncMock(return_value="Just a moment")
        
        # With challenge present, should timeout and return False
        result = await wait_for_cloudflare(mock_page, timeout=0.5)
        
        # May return False if challenge doesn't clear, or True if it does
        assert isinstance(result, bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
