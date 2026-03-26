"""Public API for the website-scraper package."""

from typing import Any, Tuple

from .scraper import WebScraper
from .intelligent_scraper import ScraperConfig, IntelligentScraper

from .browser import (
    PlaywrightDriver,
    PlaywrightConfig,
    StealthConfig,
    apply_stealth,
    simulate_human_behavior,
    wait_for_cloudflare,
    get_browser_args,
)

from .extractors import (
    ContentExtractor,
    ExtractedPageData,
    LinkExtractor,
    LinkInfo,
)

from .exporters import (
    BaseExporter,
    ExportConfig,
    ScrapingResult,
    ScrapingStats,
    JSONExporter,
    MarkdownExporter,
    CSVExporter,
    create_exporter,
    ExporterType,
)

from .llm import (
    BaseLLMProvider,
    LLMConfig,
    LLMProviderType,
    ExtractedContent,
    ScoredLink,
    create_llm_provider,
    get_available_providers,
    auto_detect_provider,
)

__version__ = "0.1.4"


def scrape_url(
    url: str,
    *,
    show_progress: bool = True,
    **kwargs: Any,
) -> Tuple[dict, dict]:
    """
    Run :meth:`WebScraper.scrape` starting from ``url``.

    This is a thin wrapper around :class:`WebScraper` for one-off scripts.
    """
    scraper = WebScraper(base_url=url, **kwargs)
    return scraper.scrape(show_progress=show_progress)


__all__ = [
    "WebScraper",
    "scrape_url",
    "ScraperConfig",
    "IntelligentScraper",
    "PlaywrightDriver",
    "PlaywrightConfig",
    "StealthConfig",
    "apply_stealth",
    "simulate_human_behavior",
    "wait_for_cloudflare",
    "get_browser_args",
    "ContentExtractor",
    "ExtractedPageData",
    "LinkExtractor",
    "LinkInfo",
    "BaseExporter",
    "ExportConfig",
    "ScrapingResult",
    "ScrapingStats",
    "JSONExporter",
    "MarkdownExporter",
    "CSVExporter",
    "create_exporter",
    "ExporterType",
    "BaseLLMProvider",
    "LLMConfig",
    "LLMProviderType",
    "ExtractedContent",
    "ScoredLink",
    "create_llm_provider",
    "get_available_providers",
    "auto_detect_provider",
    "__version__",
]
