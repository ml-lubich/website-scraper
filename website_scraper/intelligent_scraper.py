"""Intelligent web scraper with Playwright, LLM, and advanced extraction."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, cast
from pathlib import Path
from urllib.parse import urlparse, urljoin

from .browser import PlaywrightDriver, PlaywrightConfig, StealthConfig
from .extractors import ContentExtractor, LinkExtractor, ExtractedPageData, LinkInfo
from .llm import BaseLLMProvider, LLMConfig, create_llm_provider, LLMProviderType
from .exporters import BaseExporter, ExportConfig, create_exporter, ExporterType
from .exporters.base import ScrapingResult, ScrapingStats

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration for the intelligent scraper."""
    
    # Basic settings
    base_url: str
    max_pages: int = 100
    max_depth: int = 5
    same_domain_only: bool = True
    
    # Browser settings
    browser_config: Optional[PlaywrightConfig] = None
    use_browser: bool = True  # Use Playwright instead of requests
    
    # LLM settings
    llm_provider: Optional[str] = None  # "openai", "anthropic", "gemini", or None
    llm_config: Optional[LLMConfig] = None
    use_llm: bool = False  # Enable LLM-powered extraction
    
    # Extraction settings
    remove_noise: bool = True
    min_content_length: int = 100
    
    # Export settings
    export_format: str = "json"  # "json", "markdown", "csv"
    output_path: Optional[str] = None
    
    # Crawling settings
    delay_range: tuple = (1, 3)  # Random delay between requests
    max_retries: int = 3
    timeout: int = 30
    
    # Logging
    log_dir: str = "logs"
    verbose: bool = True


class IntelligentScraper:
    """
    Intelligent web scraper with Playwright browser automation,
    optional LLM-powered content extraction, and multiple export formats.
    
    This scraper can:
    - Use Playwright for JavaScript-heavy sites and Cloudflare bypass
    - Use LLM to intelligently extract and classify content
    - Filter and prioritize links based on relevance
    - Export data in multiple formats (JSON, Markdown, CSV)
    """
    
    def __init__(self, config: ScraperConfig):
        """
        Initialize the intelligent scraper.
        
        Args:
            config: Scraper configuration
        """
        self.config = config
        self.base_domain = urlparse(config.base_url).netloc
        
        # Initialize components
        self.content_extractor = ContentExtractor(remove_noise=config.remove_noise)
        self.link_extractor = LinkExtractor(base_url=config.base_url)
        
        # Initialize LLM if enabled
        self.llm_provider: Optional[BaseLLMProvider] = None
        if config.use_llm and config.llm_provider:
            try:
                self.llm_provider = create_llm_provider(
                    config.llm_provider,
                    config.llm_config or LLMConfig(),
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM provider: {str(e)}")
                self.llm_provider = None
        
        # Initialize exporter
        export_config = ExportConfig(output_path=config.output_path)
        self.exporter = create_exporter(config.export_format, export_config)
        
        # Crawling state
        self.visited_urls: Set[str] = set()
        self.scraped_data: Dict[str, Any] = {}
        self.failed_urls: List[str] = []
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        if not logger.handlers:
            handler = logging.FileHandler(
                log_dir / f"scraper_{int(time.time())}.log"
            )
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)
    
    async def scrape(self) -> Dict[str, Any]:
        """
        Start scraping the website.
        
        Returns:
            Dictionary with 'data' and 'stats' keys
        """
        start_time = time.time()
        
        # Use browser if configured
        if self.config.use_browser:
            await self._scrape_with_browser()
        else:
            # Fallback to requests-based scraping (from old scraper)
            logger.warning("Browser mode disabled, using basic requests (limited functionality)")
            # For now, we'll use browser mode as default
        
        duration = time.time() - start_time
        
        # Build statistics
        stats = {
            "total_pages_scraped": len(self.scraped_data),
            "total_urls_visited": len(self.visited_urls),
            "failed_urls": len(self.failed_urls),
            "start_url": self.config.base_url,
            "duration_seconds": round(duration, 2),
            "duration_formatted": self._format_duration(duration),
            "success_rate": f"{(len(self.scraped_data) / len(self.visited_urls) * 100):.1f}%" if self.visited_urls else "0%",
        }
        
        return {
            "data": self.scraped_data,
            "stats": stats,
        }
    
    async def _scrape_with_browser(self) -> None:
        """Scrape using Playwright browser."""
        browser_config = self.config.browser_config or PlaywrightConfig()
        
        async with PlaywrightDriver(browser_config) as driver:
            # Start with base URL
            url_queue: List[tuple[str, int]] = [(self.config.base_url, 0)]  # (url, depth)
            
            while url_queue and len(self.visited_urls) < self.config.max_pages:
                # Get next URL
                current_url, depth = url_queue.pop(0)
                
                # Skip if already visited or too deep
                if current_url in self.visited_urls or depth > self.config.max_depth:
                    continue
                
                # Check domain restriction
                if self.config.same_domain_only:
                    url_domain = urlparse(current_url).netloc
                    if url_domain != self.base_domain:
                        continue
                
                try:
                    # Create new page
                    page = await driver.new_page()
                    
                    # Navigate to URL
                    response = await driver.goto(
                        page,
                        current_url,
                        wait_for="networkidle",
                        simulate_human=True,
                        handle_cloudflare=True,
                    )
                    
                    if response and response.status == 200:
                        # Get page content
                        html = await driver.get_page_content(page)
                        
                        # Extract data
                        page_data = await self._extract_page_data(current_url, html)
                        
                        if page_data:
                            self.scraped_data[current_url] = page_data.to_dict()
                            self.visited_urls.add(current_url)
                            
                            # Extract and analyze links
                            links = await self._extract_and_analyze_links(
                                current_url,
                                html,
                                page_data,
                            )
                            
                            # Add new links to queue
                            for link in links:
                                if link.follow and link.url not in self.visited_urls:
                                    url_queue.append((link.url, depth + 1))
                            
                            logger.info(f"Scraped {current_url} ({len(self.scraped_data)}/{self.config.max_pages})")
                        else:
                            self.failed_urls.append(current_url)
                    else:
                        self.failed_urls.append(current_url)
                        logger.warning(f"Failed to load {current_url}")
                    
                    # Close page
                    await page.close()
                    
                    # Delay between requests
                    await asyncio.sleep(self._get_random_delay())
                    
                except Exception as e:
                    logger.error(f"Error scraping {current_url}: {str(e)}")
                    self.failed_urls.append(current_url)
                    continue
    
    async def _extract_page_data(self, url: str, html: str) -> Optional[ExtractedPageData]:
        """Extract structured data from a page."""
        try:
            # Basic extraction
            page_data = self.content_extractor.extract(html, url)
            
            # Enhance with LLM if available
            if self.llm_provider and self.config.use_llm:
                try:
                    llm_content = await self.llm_provider.analyze_content(
                        html,
                        url,
                    )
                    
                    # Merge LLM results
                    if llm_content.main_content:
                        page_data.main_content = llm_content.main_content
                    if llm_content.title:
                        page_data.title = llm_content.title
                    if llm_content.summary:
                        page_data.description = llm_content.summary
                    if llm_content.content_type:
                        page_data.content_type = llm_content.content_type
                    if llm_content.author:
                        page_data.author = llm_content.author
                    if llm_content.date_published:
                        page_data.date_published = llm_content.date_published
                    
                except Exception as e:
                    logger.warning(f"LLM extraction failed for {url}: {str(e)}")
            
            # Filter by content length
            if len(page_data.main_content) < self.config.min_content_length:
                return None
            
            return page_data
            
        except Exception as e:
            logger.error(f"Failed to extract data from {url}: {str(e)}")
            return None
    
    async def _extract_and_analyze_links(
        self,
        url: str,
        html: str,
        page_data: ExtractedPageData,
    ) -> List[LinkInfo]:
        """Extract and analyze links from a page."""
        # Basic link extraction
        links = self.link_extractor.extract(html, url)
        
        # Enhance with LLM if available
        if self.llm_provider and self.config.use_llm:
            try:
                # Convert to dict format for LLM
                links_dict = [
                    {"url": link.url, "text": link.text}
                    for link in links
                ]
                
                # Get page context
                page_context = f"Title: {page_data.title}\nSummary: {page_data.description}"
                
                # Analyze links with LLM
                scored_links = await self.llm_provider.analyze_links(
                    links_dict,
                    page_context,
                )
                
                # Merge scores back into LinkInfo objects
                scored_dict = {sl.url: sl for sl in scored_links}
                for link in links:
                    if link.url in scored_dict:
                        scored = scored_dict[link.url]
                        link.link_type = scored.link_type
                        link.follow = scored.should_follow
                        # Store relevance score if needed
                        setattr(link, "relevance_score", scored.relevance_score)
                
                # Sort by relevance
                links.sort(
                    key=lambda x: getattr(x, "relevance_score", 0.5),
                    reverse=True,
                )
                
            except Exception as e:
                logger.warning(f"LLM link analysis failed for {url}: {str(e)}")
        
        return links
    
    def _get_random_delay(self) -> float:
        """Get random delay between requests."""
        import random
        min_delay, max_delay = self.config.delay_range
        return random.uniform(min_delay, max_delay)
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def _dict_to_scraping_results(self, data: Dict[str, Any]) -> List[ScrapingResult]:
        """Map internal scrape dict to exporter rows."""
        rows: List[ScrapingResult] = []
        for url, payload in data.items():
            if not isinstance(payload, dict):
                continue
            rows.append(
                ScrapingResult(
                    url=url,
                    title=str(payload.get("title") or ""),
                    content=str(
                        payload.get("main_content")
                        or payload.get("text")
                        or ""
                    ),
                    meta_description=payload.get("meta_description"),
                )
            )
        return rows

    def _dict_to_scraping_stats(self, stats: Dict[str, Any]) -> ScrapingStats:
        """Map stats dict from :meth:`scrape` to :class:`ScrapingStats`."""
        start_url = str(stats.get("start_url") or self.config.base_url)
        domain = urlparse(start_url).netloc
        total_ok = int(stats.get("total_pages_scraped", len(self.scraped_data)))
        failed = int(stats.get("failed_urls", 0))
        visited = int(stats.get("total_urls_visited", total_ok + failed))
        return ScrapingStats(
            total_pages=visited,
            successful_pages=total_ok,
            failed_pages=failed,
            start_url=start_url,
            domain=domain,
            duration_seconds=float(stats.get("duration_seconds", 0.0)),
        )

    async def export(
        self,
        data: Dict[str, Any],
        stats: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Export scraped data using the configured exporter.

        Args:
            data: Scraped page data (URL -> payload dict)
            stats: Optional statistics from :meth:`scrape`

        Returns:
            Path to exported file
        """
        results_list = self._dict_to_scraping_results(data)
        stats_obj = self._dict_to_scraping_stats(stats) if stats else None
        output_path = self.config.output_path
        if not output_path:
            ext = cast(str, self.exporter.file_extension)
            output_path = str(Path(self.config.log_dir) / f"export{ext}")
        written = await self.exporter.export_to_file(
            results_list,
            output_path,
            stats_obj,
        )
        return Path(written)

    async def scrape_and_export(self) -> Path:
        """
        Scrape website and export results.

        Returns:
            Path to exported file
        """
        results = await self.scrape()
        return await self.export(results["data"], results["stats"])
