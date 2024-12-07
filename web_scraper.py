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
from multiprocessing import Manager
from tqdm import tqdm
import math

class WebScraper:
    def __init__(self, base_url: str, 
                 delay_range: tuple = (1, 3),
                 max_retries: int = 3,
                 log_dir: str = 'logs',
                 verbose: bool = True,
                 max_workers: int = None):
        
        # Initialize standard components first
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.verbose = verbose
        self.max_workers = max_workers or mp.cpu_count()
        
        # Create logs directory first
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped log filename
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f'{timestamp}.log'
        
        # Initialize logger
        self.logger = self._setup_logger()
        
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
        """Configure logging with file handler."""
        try:
            logger = logging.getLogger('WebScraper')
            logger.setLevel(logging.DEBUG)

            # Clear any existing handlers
            if logger.handlers:
                logger.handlers.clear()

            # Ensure parent directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # File handler with rotation
            file_handler = logging.handlers.RotatingFileHandler(
                str(self.log_file),
                maxBytes=1024*1024, 
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'))
            
            logger.addHandler(file_handler)
            return logger
            
        except Exception as e:
            raise Exception(f"Failed to setup logger: {str(e)}")

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

    def _make_request(self, url: str, session: requests.Session) -> Optional[requests.Response]:
        """Make request with consistent browser-like behavior."""
        for attempt in range(self.max_retries):
            try:
                session.headers.update(self._get_headers())
                timeout = max(10, random.uniform(10, 30))
                
                # Ensure positive delay
                delay = max(0.1, self._get_random_delay())
                time.sleep(delay)
                
                response = session.get(
                    url,
                    timeout=timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                self.logger.debug(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    # Ensure positive backoff delay
                    backoff_delay = max(0.1, self._get_random_delay() * 2)
                    time.sleep(backoff_delay)
                continue
            
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
        """Extract relevant data from the page. Override this method for custom extraction."""
        return {
            'title': soup.title.string if soup.title else None,
            'text': soup.get_text(separator=' ', strip=True),
            'meta_description': soup.find('meta', {'name': 'description'})['content'] 
                if soup.find('meta', {'name': 'description'}) else None
        }

    def _process_url(self, url: str, shared_visited: list) -> tuple[str, dict, list]:
        """Process URL with varied session parameters."""
        if url in shared_visited:
            return url, None, []

        session = requests.Session()
        
        # Randomize session parameters
        session.verify = True
        session.stream = random.choice([True, False])
        
        try:
            response = self._make_request(url, session)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                page_data = self._extract_data(soup)
                new_links = self._extract_links(soup, url)
                return url, page_data, new_links
                
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
            
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
        """Main scraping method using multiprocessing with progress tracking."""
        # Add start_time at the beginning of the method
        start_time = time.time()
        
        with Manager() as manager:
            shared_visited = manager.list()
            shared_results = manager.dict()
            url_queue = manager.list([self.base_url])
            shared_progress = manager.Value('i', 0)
            
            total_estimate = 10
            
            if show_progress:
                pbar = tqdm(
                    total=total_estimate,
                    desc="Scraping progress",
                    unit="pages",
                    dynamic_ncols=True,
                    leave=True,
                    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} ['
                              'Elapsed: {elapsed}, Remaining: {remaining}]'
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
                            pbar.total = total_estimate
                        
                        for link in new_unseen_links:
                            url_queue.append(link)

                        if pbar:
                            pbar.n = shared_progress.value
                            pbar.refresh()
                        
                        self.logger.info(
                            f"Progress: {(shared_progress.value/total_estimate)*100:.1f}% "
                            f"({shared_progress.value}/{total_estimate}) - Queue: {len(url_queue)}"
                        )

            # Ensure progress bar shows 100%
            if pbar:
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
                "success_rate": f"{(len(shared_results) / len(shared_visited) * 100):.1f}%" if shared_visited else "0%"
            }
            
            return dict(shared_results), stats

def main():
    parser = argparse.ArgumentParser(description='Web Scraper CLI')
    parser.add_argument('url', help='Base URL to scrape')
    parser.add_argument('--min-delay', type=float, default=1.0,
                      help='Minimum delay between requests (seconds)')
    parser.add_argument('--max-delay', type=float, default=3.0,
                      help='Maximum delay between requests (seconds)')
    parser.add_argument('--retries', type=int, default=3,
                      help='Maximum number of retry attempts')
    parser.add_argument('--workers', type=int, default=None,
                      help='Number of worker processes (default: CPU count)')
    parser.add_argument('--log-dir', type=str, default='logs',
                      help='Directory to store log files')
    parser.add_argument('--output', type=str,
                      help='Output file path for scraped data (JSON)')
    parser.add_argument('--quiet', action='store_true',
                      help='Suppress progress bar')

    args = parser.parse_args()

    try:
        # Create log directory first
        log_dir = Path(args.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        scraper = WebScraper(
            base_url=args.url,
            delay_range=(args.min_delay, args.max_delay),
            max_retries=args.retries,
            log_dir=str(log_dir),  # Convert Path to string
            max_workers=args.workers
        )

        data, stats = scraper.scrape(show_progress=not args.quiet)
        
        # Print summary and handle output as before
        print("\nScraping Summary:", file=sys.stderr)
        print("-----------------", file=sys.stderr)
        print(f"Start URL: {stats['start_url']}", file=sys.stderr)
        print(f"Total Pages Scraped: {stats['total_pages_scraped']}", file=sys.stderr)
        print(f"Total URLs Processed: {stats['total_urls_processed']}", file=sys.stderr)
        print(f"Failed URLs: {stats['failed_urls']}", file=sys.stderr)
        print(f"Success Rate: {stats['success_rate']}", file=sys.stderr)
        print(f"Duration: {stats['duration']}", file=sys.stderr)
        print("-----------------", file=sys.stderr)

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
            print(f"\nData saved to: {output_path}", file=sys.stderr)
        else:
            # Print only the JSON output to stdout
            print(json.dumps(output, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\nFatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()