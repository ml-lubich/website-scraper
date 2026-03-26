"""Stealth configuration and human-like behavior simulation for Cloudflare bypass."""

import asyncio
import random
import math
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from playwright.async_api import Page, BrowserContext


@dataclass
class StealthConfig:
    """Configuration for stealth browser behavior."""
    
    # Viewport settings - common desktop resolutions
    viewport_sizes: List[Tuple[int, int]] = field(default_factory=lambda: [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (2560, 1440),
    ])
    
    # Locales for natural browsing appearance
    locales: List[str] = field(default_factory=lambda: [
        "en-US",
        "en-GB",
        "en-CA",
        "en-AU",
    ])
    
    # Timezones matching locales
    timezones: List[str] = field(default_factory=lambda: [
        "America/New_York",
        "America/Chicago",
        "America/Los_Angeles",
        "America/Denver",
        "Europe/London",
    ])
    
    # User agents - modern Chrome versions
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ])
    
    # Delay configuration (seconds)
    min_delay: float = 1.0
    max_delay: float = 3.0
    
    # Human behavior settings
    enable_mouse_movements: bool = True
    enable_scrolling: bool = True
    enable_reading_delay: bool = True
    
    def get_random_viewport(self) -> Tuple[int, int]:
        """Get a random viewport size."""
        return random.choice(self.viewport_sizes)
    
    def get_random_locale(self) -> str:
        """Get a random locale."""
        return random.choice(self.locales)
    
    def get_random_timezone(self) -> str:
        """Get a random timezone."""
        return random.choice(self.timezones)
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent."""
        return random.choice(self.user_agents)
    
    def get_random_delay(self) -> float:
        """Get a random delay using gaussian distribution for more natural timing."""
        mean = (self.min_delay + self.max_delay) / 2
        std_dev = (self.max_delay - self.min_delay) / 4
        delay = random.gauss(mean, std_dev)
        return max(self.min_delay, min(self.max_delay, delay))


# JavaScript to inject for stealth - removes automation indicators
STEALTH_JS = """
() => {
    // Remove webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    // Mock plugins array
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            },
            {
                0: {type: "application/pdf", suffixes: "pdf", description: ""},
                description: "",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                length: 1,
                name: "Chrome PDF Viewer"
            }
        ],
    });
    
    // Mock languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });
    
    // Mock permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // Override chrome object
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {}
    };
    
    // Mock WebGL vendor and renderer
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };
    
    // Remove automation-related properties from window
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    
    // Modify the toString methods to hide our changes
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === navigator.permissions.query) {
            return 'function query() { [native code] }';
        }
        return originalToString.call(this);
    };
}
"""


async def apply_stealth(context: BrowserContext, config: Optional[StealthConfig] = None) -> None:
    """
    Apply stealth settings to a browser context.
    
    This injects JavaScript to mask automation indicators that Cloudflare
    and other bot detection systems look for.
    
    Args:
        context: Playwright browser context to apply stealth to
        config: Optional stealth configuration
    """
    config = config or StealthConfig()
    
    # Add initialization script that runs on every page
    await context.add_init_script(STEALTH_JS)


async def simulate_human_behavior(
    page: Page,
    config: Optional[StealthConfig] = None,
    scroll_page: bool = True,
) -> None:
    """
    Simulate human-like behavior on a page.
    
    This includes random mouse movements, natural scrolling patterns,
    and reading delays based on content length.
    
    Args:
        page: Playwright page to simulate behavior on
        config: Optional stealth configuration
        scroll_page: Whether to scroll the page
    """
    config = config or StealthConfig()
    
    # Wait for page to be interactive
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass  # Continue even if timeout
    
    # Random mouse movements
    if config.enable_mouse_movements:
        await _perform_random_mouse_movements(page)
    
    # Natural scrolling
    if config.enable_scrolling and scroll_page:
        await _perform_natural_scroll(page, config)
    
    # Reading delay based on content
    if config.enable_reading_delay:
        await _simulate_reading_delay(page, config)


async def _perform_random_mouse_movements(page: Page, num_movements: int = 3) -> None:
    """Perform random mouse movements to simulate human cursor behavior."""
    try:
        viewport = page.viewport_size
        if not viewport:
            return
            
        width, height = viewport["width"], viewport["height"]
        
        for _ in range(num_movements):
            # Generate random target position
            target_x = random.randint(100, width - 100)
            target_y = random.randint(100, height - 100)
            
            # Move mouse with slight randomization
            await page.mouse.move(
                target_x + random.uniform(-10, 10),
                target_y + random.uniform(-10, 10),
            )
            
            # Small delay between movements
            await asyncio.sleep(random.uniform(0.1, 0.3))
    except Exception:
        pass  # Ignore mouse movement errors


async def _perform_natural_scroll(page: Page, config: StealthConfig) -> None:
    """Perform natural scrolling pattern - humans don't scroll linearly."""
    try:
        # Get page height
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = page.viewport_size["height"] if page.viewport_size else 800
        
        if page_height <= viewport_height:
            return  # No need to scroll
        
        # Calculate scroll distance (don't scroll all the way)
        max_scroll = min(page_height * 0.7, 3000)  # Cap at 70% or 3000px
        current_position = 0
        
        while current_position < max_scroll:
            # Variable scroll amount (humans scroll in chunks)
            scroll_amount = random.randint(100, 400)
            
            # Sometimes pause mid-scroll (reading behavior)
            if random.random() < 0.3:
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Smooth scroll
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            current_position += scroll_amount
            
            # Natural delay between scrolls
            await asyncio.sleep(random.uniform(0.1, 0.4))
        
        # Sometimes scroll back up slightly
        if random.random() < 0.3:
            await page.evaluate(f"window.scrollBy(0, -{random.randint(50, 200)})")
            
    except Exception:
        pass  # Ignore scroll errors


async def _simulate_reading_delay(page: Page, config: StealthConfig) -> None:
    """Simulate reading time based on page content length."""
    try:
        # Get text content length
        text_length = await page.evaluate("""
            () => {
                const text = document.body.innerText || '';
                return text.length;
            }
        """)
        
        # Calculate reading time (average reading speed: ~250 words/min, ~5 chars/word)
        # But cap it to reasonable bounds
        estimated_words = text_length / 5
        reading_time = min(estimated_words / 250 * 60, 5)  # Cap at 5 seconds
        reading_time = max(reading_time, config.min_delay)
        
        # Add some randomness
        actual_delay = reading_time * random.uniform(0.5, 1.5)
        actual_delay = min(actual_delay, config.max_delay * 2)
        
        await asyncio.sleep(actual_delay)
        
    except Exception:
        # Fallback to simple delay
        await asyncio.sleep(config.get_random_delay())


async def wait_for_cloudflare(page: Page, timeout: float = 30.0) -> bool:
    """
    Wait for Cloudflare challenge to be resolved.
    
    Detects common Cloudflare challenge indicators and waits for them to clear.
    
    Args:
        page: Playwright page that might have Cloudflare challenge
        timeout: Maximum time to wait for challenge resolution
        
    Returns:
        True if page loaded successfully, False if still blocked
    """
    cloudflare_indicators = [
        "Checking your browser",
        "Please Wait",
        "Just a moment",
        "Attention Required",
        "cf-browser-verification",
        "cf-challenge",
    ]
    
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        try:
            # Check page content for Cloudflare indicators
            content = await page.content()
            title = await page.title()
            
            is_cloudflare = any(
                indicator.lower() in content.lower() or indicator.lower() in title.lower()
                for indicator in cloudflare_indicators
            )
            
            if not is_cloudflare:
                return True
            
            # Wait and check again
            await asyncio.sleep(2)
            
        except Exception:
            await asyncio.sleep(1)
    
    return False


def get_browser_args(headless: bool = True) -> List[str]:
    """
    Get browser launch arguments optimized for stealth.
    
    Args:
        headless: Whether to run in headless mode
        
    Returns:
        List of browser arguments
    """
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-component-extensions-with-background-pages",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-features=TranslateUI",
        "--disable-hang-monitor",
        "--disable-ipc-flooding-protection",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost",
        "--disable-renderer-backgrounding",
        "--disable-sync",
        "--enable-features=NetworkService,NetworkServiceInProcess",
        "--force-color-profile=srgb",
        "--metrics-recording-only",
        "--no-first-run",
        "--password-store=basic",
        "--use-mock-keychain",
        "--export-tagged-pdf",
    ]
    
    if headless:
        args.extend([
            "--headless=new",
        ])
    
    return args

