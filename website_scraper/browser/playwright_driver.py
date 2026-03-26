"""Playwright browser driver with stealth capabilities."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, Literal, AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
    Response,
    Error as PlaywrightError,
)

from .stealth import (
    StealthConfig,
    apply_stealth,
    simulate_human_behavior,
    wait_for_cloudflare,
    get_browser_args,
)


logger = logging.getLogger(__name__)

BrowserType = Literal["chromium", "firefox", "webkit"]


@dataclass
class PlaywrightConfig:
    """Configuration for Playwright browser driver."""
    
    browser_type: BrowserType = "chromium"
    headless: bool = True
    stealth_config: StealthConfig = field(default_factory=StealthConfig)
    
    # Timeout settings (milliseconds)
    default_timeout: int = 30000
    navigation_timeout: int = 60000
    
    # Download settings
    downloads_path: Optional[str] = None
    
    # Proxy settings
    proxy: Optional[dict] = None
    
    # Screenshot settings
    screenshot_on_error: bool = True
    screenshot_path: Optional[str] = None
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 2.0


class PlaywrightDriver:
    """
    Async Playwright browser driver with stealth capabilities.
    
    This class provides a high-level interface for browser automation
    with built-in stealth features to bypass bot detection.
    
    Usage:
        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            await driver.goto(page, "https://example.com")
            content = await page.content()
    """
    
    def __init__(self, config: Optional[PlaywrightConfig] = None):
        """
        Initialize the Playwright driver.
        
        Args:
            config: Optional configuration for the driver
        """
        self.config = config or PlaywrightConfig()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._pages: list[Page] = []
    
    async def __aenter__(self) -> "PlaywrightDriver":
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Start the Playwright browser."""
        logger.info(f"Starting Playwright with {self.config.browser_type} browser")
        
        self._playwright = await async_playwright().start()
        
        # Select browser type
        browser_launcher = getattr(self._playwright, self.config.browser_type)
        
        # Get stealth browser arguments
        args = get_browser_args(self.config.headless)
        
        # Launch browser
        self._browser = await browser_launcher.launch(
            headless=self.config.headless,
            args=args,
        )
        
        # Create browser context with stealth settings
        viewport = self.config.stealth_config.get_random_viewport()
        context_options = {
            "viewport": {"width": viewport[0], "height": viewport[1]},
            "user_agent": self.config.stealth_config.get_random_user_agent(),
            "locale": self.config.stealth_config.get_random_locale(),
            "timezone_id": self.config.stealth_config.get_random_timezone(),
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "color_scheme": "light",
        }
        
        if self.config.proxy:
            context_options["proxy"] = self.config.proxy
        
        if self.config.downloads_path:
            context_options["accept_downloads"] = True
        
        self._context = await self._browser.new_context(**context_options)
        
        # Set default timeouts
        self._context.set_default_timeout(self.config.default_timeout)
        self._context.set_default_navigation_timeout(self.config.navigation_timeout)
        
        # Apply stealth scripts
        await apply_stealth(self._context, self.config.stealth_config)
        
        logger.info("Playwright browser started successfully")
    
    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        logger.info("Closing Playwright browser")
        
        # Close all pages
        for page in self._pages:
            try:
                await page.close()
            except Exception:
                pass
        self._pages.clear()
        
        # Close context
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
        
        # Close browser
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        
        # Stop playwright
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        
        logger.info("Playwright browser closed")
    
    async def new_page(self) -> Page:
        """
        Create a new browser page.
        
        Returns:
            New Playwright page
        """
        if not self._context:
            raise RuntimeError("Browser not started. Call start() first or use async context manager.")
        
        page = await self._context.new_page()
        self._pages.append(page)
        
        return page
    
    async def goto(
        self,
        page: Page,
        url: str,
        wait_for: Literal["load", "domcontentloaded", "networkidle"] = "networkidle",
        simulate_human: bool = True,
        handle_cloudflare: bool = True,
    ) -> Optional[Response]:
        """
        Navigate to a URL with retry logic and human simulation.
        
        Args:
            page: Page to navigate
            url: URL to navigate to
            wait_for: Load state to wait for
            simulate_human: Whether to simulate human behavior after loading
            handle_cloudflare: Whether to wait for Cloudflare challenges
            
        Returns:
            Response object or None if navigation failed
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Navigating to {url} (attempt {attempt + 1}/{self.config.max_retries})")
                
                response = await page.goto(url, wait_until=wait_for)
                
                # Handle Cloudflare challenge
                if handle_cloudflare:
                    cloudflare_passed = await wait_for_cloudflare(page, timeout=30.0)
                    if not cloudflare_passed:
                        logger.warning(f"Cloudflare challenge not resolved for {url}")
                
                # Simulate human behavior
                if simulate_human:
                    await simulate_human_behavior(page, self.config.stealth_config)
                
                logger.debug(f"Successfully loaded {url}")
                return response
                
            except PlaywrightError as e:
                last_error = e
                logger.warning(f"Navigation error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error navigating to {url}: {str(e)}")
                break
        
        # Take error screenshot if configured
        if self.config.screenshot_on_error and self.config.screenshot_path:
            try:
                screenshot_file = Path(self.config.screenshot_path) / f"error_{url.replace('/', '_')[:50]}.png"
                await page.screenshot(path=str(screenshot_file))
                logger.debug(f"Error screenshot saved to {screenshot_file}")
            except Exception:
                pass
        
        logger.error(f"Failed to navigate to {url} after {self.config.max_retries} attempts: {last_error}")
        return None
    
    async def get_page_content(self, page: Page) -> str:
        """
        Get the full HTML content of a page.
        
        Args:
            page: Page to get content from
            
        Returns:
            HTML content as string
        """
        return await page.content()
    
    async def get_text_content(self, page: Page) -> str:
        """
        Get the text content of a page (no HTML tags).
        
        Args:
            page: Page to get text from
            
        Returns:
            Text content as string
        """
        return await page.evaluate("() => document.body.innerText || ''")
    
    async def get_title(self, page: Page) -> str:
        """
        Get the page title.
        
        Args:
            page: Page to get title from
            
        Returns:
            Page title
        """
        return await page.title()
    
    async def extract_links(self, page: Page, same_domain: bool = True) -> list[dict]:
        """
        Extract all links from a page.
        
        Args:
            page: Page to extract links from
            same_domain: If True, only return links from the same domain
            
        Returns:
            List of link dictionaries with href, text, and is_internal keys
        """
        current_url = page.url
        
        links = await page.evaluate("""
            (currentUrl) => {
                const currentDomain = new URL(currentUrl).hostname;
                const links = [];
                
                document.querySelectorAll('a[href]').forEach(anchor => {
                    try {
                        const href = anchor.href;
                        const url = new URL(href, currentUrl);
                        const isInternal = url.hostname === currentDomain;
                        
                        links.push({
                            href: url.href,
                            text: anchor.innerText.trim().substring(0, 200),
                            is_internal: isInternal,
                        });
                    } catch (e) {
                        // Invalid URL, skip
                    }
                });
                
                return links;
            }
        """, current_url)
        
        if same_domain:
            links = [link for link in links if link.get("is_internal", False)]
        
        # Deduplicate by href
        seen = set()
        unique_links = []
        for link in links:
            if link["href"] not in seen:
                seen.add(link["href"])
                unique_links.append(link)
        
        return unique_links
    
    async def take_screenshot(
        self,
        page: Page,
        path: Optional[str] = None,
        full_page: bool = False,
    ) -> bytes:
        """
        Take a screenshot of the page.
        
        Args:
            page: Page to screenshot
            path: Optional path to save screenshot
            full_page: Whether to capture the full scrollable page
            
        Returns:
            Screenshot as bytes
        """
        screenshot_options = {"full_page": full_page}
        if path:
            screenshot_options["path"] = path
        
        return await page.screenshot(**screenshot_options)
    
    async def wait_for_selector(
        self,
        page: Page,
        selector: str,
        timeout: int = 10000,
    ) -> bool:
        """
        Wait for a selector to appear on the page.
        
        Args:
            page: Page to wait on
            selector: CSS selector to wait for
            timeout: Maximum wait time in milliseconds
            
        Returns:
            True if selector found, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
    
    async def execute_script(self, page: Page, script: str) -> any:
        """
        Execute JavaScript on the page.
        
        Args:
            page: Page to execute script on
            script: JavaScript code to execute
            
        Returns:
            Result of script execution
        """
        return await page.evaluate(script)
    
    @property
    def is_running(self) -> bool:
        """Check if the browser is running."""
        return self._browser is not None and self._context is not None


@asynccontextmanager
async def create_page(
    config: Optional[PlaywrightConfig] = None,
) -> AsyncIterator[tuple[PlaywrightDriver, Page]]:
    """
    Convenience context manager to create a driver and page in one step.
    
    Usage:
        async with create_page() as (driver, page):
            await driver.goto(page, "https://example.com")
            content = await page.content()
    
    Args:
        config: Optional Playwright configuration
        
    Yields:
        Tuple of (PlaywrightDriver, Page)
    """
    async with PlaywrightDriver(config) as driver:
        page = await driver.new_page()
        try:
            yield driver, page
        finally:
            await page.close()

