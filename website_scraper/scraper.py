import requests
import logging
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests.exceptions import RequestException
from typing import Set, List, Optional
import logging.handlers
import fake_useragent
import argparse
import os
from pathlib import Path
import sys
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from queue import Empty
from multiprocessing import Manager, freeze_support
from tqdm import tqdm
import math
import warnings
import importlib.util
from urllib3.exceptions import InsecureRequestWarning
from bs4.builder import XMLParsedAsHTMLWarning
try:
    import lxml
except ImportError:
    pass  # Will be installed if needed in main()

# Suppress specific warnings
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

# Add logging configuration
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and above for other loggers
    handlers=[logging.NullHandler()]  # Prevent output to console
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Enable all logs for our logger

class WebScraper:
    def __init__(self, base_url: str, 
                 delay_range: tuple = (1, 3),
                 max_retries: int = 3,
                 log_dir: str = 'logs',
                 verbose: bool = True,
                 max_workers: Optional[int] = None,
                 verify_ssl: bool = True,
                 use_undetected_chrome: bool = False,
                 uc_headless: bool = True,
                 uc_page_load_timeout: int = 45,
                 uc_browser_executable_path: Optional[str] = None):
        
        # Initialize standard components first
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.verbose = verbose
        self.verify_ssl = verify_ssl
        self.use_undetected_chrome = use_undetected_chrome
        self.uc_headless = uc_headless
        self.uc_page_load_timeout = uc_page_load_timeout
        self.uc_browser_executable_path = uc_browser_executable_path
        self._uc_driver: Optional[object] = None
        
        # Create logs directory first
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped log filename
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f'{timestamp}.log'
        
        # Initialize logger
        self.logger = self._setup_logger()

        if self.use_undetected_chrome:
            if max_workers is not None and max_workers != 1:
                self.logger.warning(
                    "use_undetected_chrome is not compatible with multiprocessing; using max_workers=1"
                )
            self.max_workers = 1
        else:
            self.max_workers = max_workers if max_workers is not None else mp.cpu_count()
        
        # Common browser headers patterns
        self.headers_pool = [
            {
                # Chrome-like headers
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            },
            {
                # Firefox-like headers
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1',
            },
            {
                # Safari-like headers
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
        ]

        # Common referrers
        self.referrers = [
            'https://www.google.com/search?q=',
            'https://www.bing.com/search?q=',
            'https://duckduckgo.com/?q=',
            'https://www.google.com/',
            'https://www.bing.com/',
            None  # Direct visits
        ]

        # Store delay range for use in delay patterns
        self.min_delay, self.max_delay = delay_range
        self.visited_urls = set()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging with file handler and minimal console output."""
        try:
            logger = logging.getLogger('WebScraper')
            logger.setLevel(logging.DEBUG)
            logger.propagate = False  # Prevent propagation to root logger

            # Clear any existing handlers and close them properly
            if logger.handlers:
                for handler in logger.handlers:
                    handler.close()
                logger.handlers.clear()

            # Create detailed file handler for debug logs
            debug_file = self.log_dir / f'debug_{time.strftime("%Y%m%d_%H%M%S")}.log'
            debug_handler = logging.handlers.RotatingFileHandler(
                str(debug_file),
                maxBytes=1024*1024, 
                backupCount=5,
                encoding='utf-8',
                delay=True  # Delay file creation until first write
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            
            # Create file handler for info and above
            info_handler = logging.handlers.RotatingFileHandler(
                str(self.log_file),
                maxBytes=1024*1024, 
                backupCount=5,
                encoding='utf-8',
                delay=True  # Delay file creation until first write
            )
            info_handler.setLevel(logging.INFO)
            info_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            
            logger.addHandler(debug_handler)
            logger.addHandler(info_handler)
            
            return logger
            
        except Exception as e:
            raise Exception(f"Failed to setup logger: {str(e)}")

    def __del__(self):
        """Cleanup method to ensure proper closing of log files."""
        try:
            self._quit_uc_driver()
        except Exception:
            pass
        if hasattr(self, 'logger') and self.logger:
            for handler in self.logger.handlers:
                try:
                    handler.close()
                except Exception:
                    pass  # Ignore errors during cleanup

    def _get_random_delay(self) -> float:
        """Get delay using different patterns with guaranteed positive values."""
        try:
            patterns = [
                max(0.1, random.uniform(self.min_delay, self.max_delay)),
                max(0.1, random.gauss((self.min_delay + self.max_delay)/2, 0.5)),
                max(0.1, random.betavariate(2, 5) * (self.max_delay - self.min_delay) + self.min_delay)
            ]
            return max(0.1, random.choice(patterns))
        except Exception as e:
            self.logger.warning(f"Delay calculation error: {str(e)}, using default delay")
            return self.min_delay

    def _get_headers(self) -> dict:
        """Generate request headers that match common browser patterns."""
        headers = random.choice(self.headers_pool).copy()
        
        # Add random user agent matching the browser type
        ua = fake_useragent.UserAgent()
        if 'Chrome' in headers.get('Sec-Ch-Ua', ''):
            headers['User-Agent'] = ua.chrome
        elif 'DNT' in headers:  # Firefox pattern
            headers['User-Agent'] = ua.firefox
        else:  # Safari pattern
            headers['User-Agent'] = ua.safari
        
        # Add plausible referrer (with 70% probability)
        if random.random() < 0.7:
            referrer = random.choice(self.referrers)
            if referrer and '?q=' in referrer:
                # Add search-like query
                search_terms = [self.domain, 'website', 'contact', 'about']
                query = random.choice(search_terms)
                referrer = f"{referrer}{query}"
            headers['Referer'] = referrer

        # Add random viewport and screen resolution
        if random.random() < 0.5:
            headers['Viewport-Width'] = str(random.choice([1280, 1366, 1920]))
            headers['Viewport-Height'] = str(random.choice([720, 768, 1080]))
        
        return headers

    def _ensure_undetected_chromedriver_installed(self) -> None:
        if importlib.util.find_spec("undetected_chromedriver") is None:
            raise ImportError(
                "undetected-chromedriver is required for use_undetected_chrome=True. "
                'Install with: pip install "website-scraper[undetected]" '
                "or pip install undetected-chromedriver"
            )

    def _quit_uc_driver(self) -> None:
        driver = getattr(self, "_uc_driver", None)
        if driver is None:
            return
        try:
            driver.quit()
        except Exception:
            pass
        self._uc_driver = None

    def _create_uc_driver(self) -> object:
        """Build a single undetected Chrome instance (not fork-safe; one process only)."""
        self._ensure_undetected_chromedriver_installed()
        import undetected_chromedriver as uc

        options = uc.ChromeOptions()
        if self.uc_headless:
            options.add_argument("--headless=new")
        if not self.verify_ssl:
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--allow-insecure-localhost")
        if self.uc_browser_executable_path:
            options.binary_location = self.uc_browser_executable_path

        driver = uc.Chrome(options=options, use_subprocess=False)
        driver.set_page_load_timeout(self.uc_page_load_timeout)
        self._uc_driver = driver
        return driver

    def _uc_load_page(self, driver: object, url: str) -> Optional[str]:
        """Navigate with undetected Chrome and return HTML source."""
        for attempt in range(self.max_retries):
            try:
                delay = max(0.1, self._get_random_delay())
                time.sleep(delay)
                self.logger.info(
                    f"Undetected Chrome fetching {url} (attempt {attempt + 1}/{self.max_retries})"
                )
                driver.get(url)
                time.sleep(max(0.1, random.uniform(0.4, 1.2)))
                html = driver.page_source
                if html and len(html.strip()) > 0:
                    return html
                self.logger.warning(f"Empty page source for {url}")
            except Exception as exc:
                self.logger.error(f"Undetected Chrome error on attempt {attempt + 1}: {exc}")
            if attempt < self.max_retries - 1:
                backoff = max(0.1, self._get_random_delay() * 2)
                self.logger.info(f"Retrying in {backoff:.2f} seconds...")
                time.sleep(backoff)
        self.logger.error(f"All {self.max_retries} Undetected Chrome attempts failed for {url}")
        return None

    def _process_url_uc(self, driver: object, url: str) -> tuple:
        """Fetch one URL via undetected Chrome and parse HTML (single-process only)."""
        self.logger.info(f"Processing URL (undetected Chrome): {url}")
        html = self._uc_load_page(driver, url)
        if not html:
            return url, None, []

        try:
            if url.lower().endswith(".xml") or html.lstrip().startswith("<?xml"):
                soup = BeautifulSoup(html, "xml")
            else:
                soup = BeautifulSoup(html, "html.parser")
            page_data = self._extract_data(soup)
            new_links = self._extract_links(soup, url)
            self.logger.info(f"Successfully processed {url} via undetected Chrome")
            return url, page_data, new_links
        except Exception as exc:
            self.logger.error(f"Error parsing content from {url}: {exc}")
            return url, {"error": str(exc)}, []

    def _scrape_with_undetected_chrome(self, show_progress: bool = True) -> tuple:
        """Breadth-first crawl using one undetected Chrome driver (no multiprocessing)."""
        self._ensure_undetected_chromedriver_installed()
        start_time = time.time()
        visited: List[str] = []
        results: dict = {}
        url_queue: List[str] = [self.base_url]
        total_estimate = 10
        progress_count = 0

        pbar = None
        if show_progress:
            pbar = tqdm(
                total=total_estimate,
                desc="Scraping progress (undetected Chrome)",
                unit="pages",
                dynamic_ncols=True,
                leave=True,
                file=sys.stdout,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
            )

            def format_interval(t):
                return self._format_time(t)

            pbar.format_interval = format_interval

        try:
            driver = self._create_uc_driver()
            while url_queue:
                url = url_queue.pop(0)
                if url in visited:
                    continue

                u, data, new_links = self._process_url_uc(driver, url)
                visited.append(u)
                progress_count += 1
                if data:
                    results[u] = data

                new_unseen = [
                    link
                    for link in new_links
                    if link not in visited and link not in url_queue
                ]
                if new_unseen:
                    total_estimate = max(
                        total_estimate,
                        len(visited) + len(url_queue) + len(new_unseen),
                    )
                    if pbar is not None:
                        pbar.total = total_estimate
                for link in new_unseen:
                    url_queue.append(link)

                if pbar is not None:
                    pbar.n = progress_count
                    pbar.refresh()
                self.logger.info(
                    f"Progress: {(progress_count / total_estimate) * 100:.1f}% "
                    f"({progress_count}/{total_estimate}) - Queue: {len(url_queue)}"
                )

            if pbar is not None:
                pbar.n = max(pbar.total, progress_count)
                pbar.refresh()
                pbar.close()

            self.visited_urls.update(visited)
            duration = time.time() - start_time
            stats = {
                "total_pages_scraped": len(results),
                "total_urls_processed": len(visited),
                "failed_urls": len(visited) - len(results),
                "start_url": self.base_url,
                "duration": self._format_time(duration),
                "success_rate": f"{(len(results) / len(visited) * 100):.1f}%"
                if visited
                else "0%",
                "fetch_mode": "undetected_chrome",
            }
            return results, stats
        finally:
            self._quit_uc_driver()

    def _make_request(self, url: str, session: requests.Session) -> Optional[requests.Response]:
        """Make request with consistent browser-like behavior and enhanced logging."""
        for attempt in range(self.max_retries):
            try:
                session.headers.update(self._get_headers())
                timeout = max(10, random.uniform(10, 30))
                
                # Ensure positive delay
                delay = max(0.1, self._get_random_delay())
                time.sleep(delay)
                
                self.logger.info(f"Attempting request to {url} (attempt {attempt + 1}/{self.max_retries})")
                self.logger.debug(f"Request headers: {session.headers}")
                
                response = session.get(
                    url,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=self.verify_ssl
                )
                
                self.logger.info(f"Response status: {response.status_code}")
                self.logger.debug(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                return response

            except requests.exceptions.SSLError as e:
                self.logger.error(f"SSL Error on attempt {attempt + 1}: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"Connection Error on attempt {attempt + 1}: {str(e)}")
            except requests.exceptions.Timeout as e:
                self.logger.error(f"Timeout Error on attempt {attempt + 1}: {str(e)}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request Error on attempt {attempt + 1}: {str(e)}")
            
            if attempt < self.max_retries - 1:
                backoff_delay = max(0.1, self._get_random_delay() * 2)
                self.logger.info(f"Retrying in {backoff_delay:.2f} seconds...")
                time.sleep(backoff_delay)
            
        self.logger.error(f"All {self.max_retries} attempts failed for URL: {url}")
        return None

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract and normalize all links from the page."""
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute_url = urljoin(current_url, href)
            
            # Only include links from the same domain
            if urlparse(absolute_url).netloc == self.domain:
                links.append(absolute_url)
        
        return list(set(links))

    def _extract_data(self, soup: BeautifulSoup) -> dict:
        """Extract relevant data from the page with better error handling."""
        data = {}
        try:
            # Extract title safely
            if soup.title:
                try:
                    data['title'] = str(soup.title.string) if soup.title.string else None
                except Exception as e:
                    self.logger.error(f"Error extracting title: {str(e)}")
                    data['title'] = None

            # Extract text safely
            try:
                # Limit text length to prevent recursion
                text = soup.get_text(separator=' ', strip=True)
                data['text'] = text[:100000] if text else None  # Limit to 100K chars
            except Exception as e:
                self.logger.error(f"Error extracting text: {str(e)}")
                data['text'] = None

            # Extract meta description safely
            try:
                meta = soup.find('meta', {'name': 'description'})
                data['meta_description'] = meta['content'] if meta and 'content' in meta.attrs else None
            except Exception as e:
                self.logger.error(f"Error extracting meta description: {str(e)}")
                data['meta_description'] = None

        except Exception as e:
            self.logger.error(f"Fatal error in data extraction: {str(e)}")
            return {'error': str(e)}

        return data

    def _process_url(self, url: str, shared_visited: list) -> tuple[str, dict, list]:
        """Process URL with enhanced error handling and logging."""
        if url in shared_visited:
            self.logger.debug(f"Skipping already visited URL: {url}")
            return url, None, []

        session = requests.Session()
        session.verify = self.verify_ssl
        
        try:
            self.logger.info(f"Processing URL: {url}")
            response = self._make_request(url, session)
            
            if response:
                try:
                    self.logger.debug(f"Parsing content from {url}")
                    
                    # Check content type for XML
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'xml' in content_type or url.endswith('.xml'):
                        # Use XML parser for XML content
                        soup = BeautifulSoup(response.text, 'xml')
                        self.logger.debug("Using XML parser for XML content")
                    else:
                        # Use HTML parser for other content
                        soup = BeautifulSoup(response.text, 'html.parser')
                        self.logger.debug("Using HTML parser for HTML content")
                    
                    self.logger.debug(f"Extracting data from {url}")
                    page_data = self._extract_data(soup)
                    
                    self.logger.debug(f"Extracting links from {url}")
                    new_links = self._extract_links(soup, url)
                    
                    self.logger.info(f"Successfully processed {url}")
                    self.logger.debug(f"Found {len(new_links)} new links")
                    
                    return url, page_data, new_links
                except Exception as e:
                    self.logger.error(f"Error processing content from {url}: {str(e)}")
                    return url, {'error': str(e)}, []
            
        except Exception as e:
            self.logger.error(f"Unexpected error processing {url}: {str(e)}")
            
        return url, None, []

    def _format_time(self, seconds: float) -> str:
        """Convert seconds to human readable time format."""
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"

    def scrape(self, show_progress: bool = True) -> tuple[dict, dict]:
        """Run crawl with ``requests`` (default) or undetected Chrome (``use_undetected_chrome``)."""
        if self.use_undetected_chrome:
            return self._scrape_with_undetected_chrome(show_progress)
        return self._scrape_with_requests_pool(show_progress)

    def _scrape_with_requests_pool(self, show_progress: bool = True) -> tuple[dict, dict]:
        """Main scraping method using multiprocessing with progress tracking."""
        start_time = time.time()
        
        with Manager() as manager:
            shared_visited = manager.list()
            shared_results = manager.dict()
            url_queue = manager.list([self.base_url])
            shared_progress = manager.Value('i', 0)
            
            total_estimate = 10
            
            if show_progress:
                # Configure progress bar to only show itself
                pbar = tqdm(
                    total=total_estimate,
                    desc="Scraping progress",
                    unit="pages",
                    dynamic_ncols=True,
                    leave=True,
                    file=sys.stdout,  # Explicitly use stdout
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}'  # Simplified format
                )
                
                def format_interval(t):
                    return self._format_time(t)
                
                pbar.format_interval = format_interval

            while url_queue:
                batch = []
                while len(batch) < self.max_workers and url_queue:
                    url = url_queue.pop(0)
                    if url not in shared_visited:
                        batch.append(url)
                
                if not batch:
                    break

                with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_url = {
                        executor.submit(self._process_url, url, shared_visited): url 
                        for url in batch
                    }

                    for future in as_completed(future_to_url):
                        url, data, new_links = future.result()
                        shared_visited.append(url)
                        
                        if data:
                            shared_results[url] = data
                        
                        shared_progress.value += 1
                        
                        new_unseen_links = [link for link in new_links 
                                          if link not in shared_visited 
                                          and link not in url_queue]
                        
                        if new_unseen_links:
                            total_estimate = max(
                                total_estimate,
                                len(shared_visited) + len(url_queue) + len(new_unseen_links)
                            )
                            if show_progress:
                                pbar.total = total_estimate
                        
                        for link in new_unseen_links:
                            url_queue.append(link)

                        if show_progress:
                            pbar.n = shared_progress.value
                            pbar.refresh()
                        
                        # Log progress to file only
                        self.logger.info(
                            f"Progress: {(shared_progress.value/total_estimate)*100:.1f}% "
                            f"({shared_progress.value}/{total_estimate}) - Queue: {len(url_queue)}"
                        )

            # Ensure progress bar shows 100% and close it
            if show_progress:
                pbar.n = pbar.total
                pbar.refresh()
                pbar.close()
            
            # Update instance visited_urls
            self.visited_urls.update(shared_visited)
            
            # Create stats dictionary
            duration = time.time() - start_time
            stats = {
                "total_pages_scraped": len(shared_results),
                "total_urls_processed": len(shared_visited),
                "failed_urls": len(shared_visited) - len(shared_results),
                "start_url": self.base_url,
                "duration": self._format_time(duration),
                "success_rate": f"{(len(shared_results) / len(shared_visited) * 100):.1f}%" if shared_visited else "0%",
                "fetch_mode": "requests",
            }
            
            return dict(shared_results), stats

def main():
    # Add Windows multiprocessing support
    if sys.platform.startswith('win'):
        freeze_support()

    parser = argparse.ArgumentParser(description='Web Scraper CLI')
    parser.add_argument('url', help='Base URL to scrape')
    parser.add_argument('-m', '--min-delay', type=float, default=1.0,
                      help='Minimum delay between requests (seconds)')
    parser.add_argument('-M', '--max-delay', type=float, default=3.0,
                      help='Maximum delay between requests (seconds)')
    parser.add_argument('-r', '--retries', type=int, default=3,
                      help='Maximum number of retry attempts')
    parser.add_argument('-w', '--workers', type=int, default=None,
                      help='Number of worker processes (default: CPU count)')
    parser.add_argument('-l', '--log-dir', type=str, default='logs',
                      help='Directory to store log files')
    parser.add_argument('-o', '--output', type=str,
                      help='Output file path for scraped data (JSON)')
    parser.add_argument('-q', '--quiet', action='store_true',
                      help='Suppress progress bar')
    parser.add_argument('-k', '--no-verify-ssl', action='store_true',
                      help='Disable SSL certificate verification (use with caution)')
    parser.add_argument(
        '--undetected-chrome',
        action='store_true',
        help='Fetch pages with undetected-chromedriver (real Chrome; requires pip install undetected-chromedriver)',
    )
    parser.add_argument(
        '--uc-headed',
        action='store_true',
        help='With --undetected-chrome, run a visible browser window (default is headless)',
    )

    args = parser.parse_args()

    try:
        # Install lxml if not present
        try:
            import lxml
        except ImportError:
            print("Installing required lxml package...", file=sys.stderr)
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "lxml"])
            print("lxml installed successfully", file=sys.stderr)

        # Create log directory first
        log_dir = Path(args.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        scraper = WebScraper(
            base_url=args.url,
            delay_range=(args.min_delay, args.max_delay),
            max_retries=args.retries,
            log_dir=str(log_dir),
            max_workers=args.workers,
            verify_ssl=not args.no_verify_ssl,
            use_undetected_chrome=args.undetected_chrome,
            uc_headless=not args.uc_headed,
        )

        data, stats = scraper.scrape(show_progress=not args.quiet)
        
        # Write summary to log file
        scraper.logger.info("\nScraping Summary:")
        scraper.logger.info("-----------------")
        scraper.logger.info(f"Start URL: {stats['start_url']}")
        scraper.logger.info(f"Total Pages Scraped: {stats['total_pages_scraped']}")
        scraper.logger.info(f"Total URLs Processed: {stats['total_urls_processed']}")
        scraper.logger.info(f"Failed URLs: {stats['failed_urls']}")
        scraper.logger.info(f"Success Rate: {stats['success_rate']}")
        scraper.logger.info(f"Duration: {stats['duration']}")
        scraper.logger.info("-----------------")

        # Handle output
        output = {
            "data": data,
            "stats": stats
        }
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            scraper.logger.info(f"Data saved to: {output_path}")
        else:
            # Print JSON to stdout
            print(json.dumps(output, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()