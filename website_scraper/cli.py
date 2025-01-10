import argparse
import sys
from pathlib import Path
import subprocess
from .scraper import WebScraper
import json

def main():
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

    args = parser.parse_args()

    try:
        # Install lxml if not present
        try:
            import lxml
        except ImportError:
            print("Installing required lxml package...", file=sys.stderr)
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
            verify_ssl=not args.no_verify_ssl
        )

        data, stats = scraper.scrape(show_progress=not args.quiet)
        
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
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 