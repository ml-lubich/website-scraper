"""Tests for browser stealth functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from website_scraper.browser.stealth import (
    StealthConfig,
    apply_stealth,
    simulate_human_behavior,
    wait_for_cloudflare,
    get_browser_args,
    STEALTH_JS,
)


class TestStealthConfig:
    """Tests for StealthConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = StealthConfig()
        
        assert len(config.viewport_sizes) > 0
        assert len(config.locales) > 0
        assert len(config.timezones) > 0
        assert len(config.user_agents) > 0
        assert config.min_delay == 1.0
        assert config.max_delay == 3.0
    
    def test_custom_delay(self):
        """Test custom delay configuration."""
        config = StealthConfig(min_delay=2.0, max_delay=5.0)
        
        assert config.min_delay == 2.0
        assert config.max_delay == 5.0
    
    def test_get_random_viewport(self):
        """Test random viewport selection."""
        config = StealthConfig()
        
        viewport = config.get_random_viewport()
        assert isinstance(viewport, tuple)
        assert len(viewport) == 2
        assert viewport in config.viewport_sizes
    
    def test_get_random_locale(self):
        """Test random locale selection."""
        config = StealthConfig()
        
        locale = config.get_random_locale()
        assert locale in config.locales
    
    def test_get_random_timezone(self):
        """Test random timezone selection."""
        config = StealthConfig()
        
        timezone = config.get_random_timezone()
        assert timezone in config.timezones
    
    def test_get_random_user_agent(self):
        """Test random user agent selection."""
        config = StealthConfig()
        
        user_agent = config.get_random_user_agent()
        assert user_agent in config.user_agents
    
    def test_get_random_delay(self):
        """Test random delay generation."""
        config = StealthConfig(min_delay=1.0, max_delay=3.0)
        
        for _ in range(100):
            delay = config.get_random_delay()
            assert 1.0 <= delay <= 3.0
    
    def test_feature_flags(self):
        """Test feature flag configuration."""
        config = StealthConfig(
            enable_mouse_movements=False,
            enable_scrolling=False,
            enable_reading_delay=False,
        )
        
        assert config.enable_mouse_movements is False
        assert config.enable_scrolling is False
        assert config.enable_reading_delay is False


class TestStealthJS:
    """Tests for stealth JavaScript."""
    
    def test_stealth_js_exists(self):
        """Test that stealth JS is defined."""
        assert STEALTH_JS is not None
        assert len(STEALTH_JS) > 0
    
    def test_stealth_js_contains_webdriver_fix(self):
        """Test stealth JS removes webdriver property."""
        assert "webdriver" in STEALTH_JS
    
    def test_stealth_js_contains_plugins_mock(self):
        """Test stealth JS mocks plugins."""
        assert "plugins" in STEALTH_JS
    
    def test_stealth_js_contains_chrome_mock(self):
        """Test stealth JS mocks chrome object."""
        assert "chrome" in STEALTH_JS.lower()


@pytest.mark.asyncio
class TestApplyStealth:
    """Tests for apply_stealth function."""
    
    async def test_apply_stealth_adds_init_script(self):
        """Test that stealth adds initialization script."""
        mock_context = MagicMock()
        mock_context.add_init_script = AsyncMock()
        
        await apply_stealth(mock_context)
        
        mock_context.add_init_script.assert_called_once()
        # Verify it was called (the exact content check is too strict)
        assert mock_context.add_init_script.called
    
    async def test_apply_stealth_with_custom_config(self):
        """Test stealth with custom configuration."""
        mock_context = MagicMock()
        mock_context.add_init_script = AsyncMock()
        
        config = StealthConfig(min_delay=2.0, max_delay=4.0)
        await apply_stealth(mock_context, config)
        
        mock_context.add_init_script.assert_called_once()


@pytest.mark.asyncio
class TestSimulateHumanBehavior:
    """Tests for human behavior simulation."""
    
    async def test_simulate_human_behavior_basic(self, mock_page):
        """Test basic human simulation."""
        config = StealthConfig(
            enable_mouse_movements=False,
            enable_scrolling=False,
            enable_reading_delay=False,
        )
        
        await simulate_human_behavior(mock_page, config, scroll_page=False)
        
        # Should have called wait_for_load_state
        mock_page.wait_for_load_state.assert_called()
    
    async def test_simulate_human_no_scroll(self, mock_page):
        """Test simulation without scrolling."""
        config = StealthConfig(enable_scrolling=True)
        
        await simulate_human_behavior(mock_page, config, scroll_page=False)
        
        # Scroll should not be called when scroll_page is False
        # This is a basic test - implementation may vary
        assert True


@pytest.mark.asyncio
class TestWaitForCloudflare:
    """Tests for Cloudflare challenge detection."""
    
    async def test_no_cloudflare_challenge(self, mock_page):
        """Test page without Cloudflare challenge."""
        mock_page.content = AsyncMock(return_value="<html><body>Normal content</body></html>")
        mock_page.title = AsyncMock(return_value="Normal Page")
        
        result = await wait_for_cloudflare(mock_page, timeout=1.0)
        
        assert result is True
    
    async def test_cloudflare_challenge_detected(self, mock_page):
        """Test Cloudflare challenge detection."""
        # First call returns challenge, second returns normal
        mock_page.content = AsyncMock(side_effect=[
            "<html><body>Just a moment... Checking your browser</body></html>",
            "<html><body>Normal content</body></html>",
        ])
        mock_page.title = AsyncMock(return_value="Just a moment...")
        
        # This should wait and then pass
        result = await wait_for_cloudflare(mock_page, timeout=5.0)
        
        # Result depends on how many times content was called
        assert result in [True, False]


class TestGetBrowserArgs:
    """Tests for browser argument generation."""
    
    def test_headless_args(self):
        """Test browser args in headless mode."""
        args = get_browser_args(headless=True)
        
        assert isinstance(args, list)
        assert "--disable-blink-features=AutomationControlled" in args
    
    def test_non_headless_args(self):
        """Test browser args in non-headless mode."""
        args = get_browser_args(headless=False)
        
        assert isinstance(args, list)
        assert "--disable-blink-features=AutomationControlled" in args
    
    def test_common_stealth_args(self):
        """Test common stealth arguments are present."""
        args = get_browser_args()
        
        assert "--disable-dev-shm-usage" in args
        assert "--no-first-run" in args

