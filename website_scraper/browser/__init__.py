"""Browser automation module with Playwright and stealth capabilities."""

from .playwright_driver import PlaywrightDriver, PlaywrightConfig
from .stealth import (
    StealthConfig,
    apply_stealth,
    simulate_human_behavior,
    wait_for_cloudflare,
    get_browser_args,
)

__all__ = [
    "PlaywrightDriver",
    "PlaywrightConfig",
    "StealthConfig",
    "apply_stealth",
    "simulate_human_behavior",
    "wait_for_cloudflare",
    "get_browser_args",
]

