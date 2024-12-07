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
        
        # Add visited_urls tracking
        self.visited_urls = set()
        # Remove ua initialization from __init__
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.verbose = verbose
        self.max_workers = max_workers or mp.cpu_count()
        
        # Create logs directory
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = self._setup_logger(self.log_dir / 'scraper.log')
        
        # Initialize session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        })

    def _setup_logger(self, log_file: str) -> logging.Logger:
        """Configure logging with file handler only."""
        logger = logging.getLogger('WebScraper')
        logger.setLevel(logging.INFO)

        # Clear any existing handlers
        if logger.handlers:
            logger.handlers.clear()

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1024*1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'))
        
        logger.addHandler(file_handler)
        return logger

    def _get_random_delay(self) -> float:
        """Generate random delay between requests."""
        return random.uniform(*self.delay_range)

    def _get_headers(self) -> dict:
        """Generate random headers for each request."""
        # Create new UserAgent instance for each request
        ua = fake_useragent.UserAgent()
        return {
            'User-Agent': ua.random,
            'Referer': self.base_url,
        }

    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and error handling."""
        for attempt in range(self.max_retries):
            try:
                # Random delay before request
                time.sleep(self._get_random_delay())
                
                # Update headers for each request
                self.session.headers.update(self._get_headers())
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response

            except RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(self._get_random_delay() * 2)

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
        """Process a single URL and return its data and new links."""
        if url in shared_visited:
            return url, None, []

        session = requests.Session()
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
        })

        self.logger.info(f"Processing: {url}")

        for attempt in range(self.max_retries):
            try:
                time.sleep(self._get_random_delay())
                headers = self._get_headers()
                response = session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                page_data = self._extract_data(soup)
                new_links = self._extract_links(soup, url)
                
                self.logger.info(f"Successfully scraped: {url}")
                return url, page_data, new_links

            except Exception as e:
                # Log errors to file only
                self.logger.error(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    return url, None, []
                time.sleep(self._get_random_delay() * 2)

        return url, None, []

    def scrape(self, show_progress: bool = True) -> tuple[dict, dict]:
        """
        Main scraping method using multiprocessing with progress tracking.
        Returns: (data_dict, stats_dict)
        """
        with Manager() as manager:
            shared_visited = manager.list()
            shared_results = manager.dict()
            url_queue = manager.list([self.base_url])
            shared_progress = manager.Value('i', 0)
            
            total_estimate = 10
            
            pbar = None
            if show_progress:
                pbar = tqdm(
                    total=total_estimate,
                    desc="Scraping progress",
                    unit="pages",
                    dynamic_ncols=True,
                    leave=True,
                    ncols=80
                )

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
            stats = {
                "total_pages_scraped": len(shared_results),
                "total_urls_processed": len(shared_visited),
                "start_url": self.base_url
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

    scraper = WebScraper(
        base_url=args.url,
        delay_range=(args.min_delay, args.max_delay),
        max_retries=args.retries,
        log_dir=args.log_dir,
        max_workers=args.workers
    )

    try:
        # Redirect stdout to devnull during scraping
        with open(os.devnull, 'w') as devnull:
            # Store the original stdout
            original_stdout = sys.stdout
            
            # Redirect stdout to devnull if not quiet
            if not args.quiet:
                sys.stdout = devnull
            
            # Get data and stats
            data, stats = scraper.scrape(show_progress=not args.quiet)
            
            # Restore original stdout
            sys.stdout = original_stdout

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
        else:
            # Print only the JSON output to stdout
            print(json.dumps(output, indent=2, ensure_ascii=False))

    except KeyboardInterrupt:
        print("\nScraping interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 