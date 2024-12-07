# Wesite Scraper

A robust, multiprocessing-enabled web scraper that can be used both as a module and as a command-line tool. Features include rate limiting, bot detection avoidance, and comprehensive logging.

## Features

- Multiprocessing support for faster scraping
- Rate limiting and random delays to avoid detection
- Rotating User-Agents
- Comprehensive logging system
- Progress tracking with progress bar
- Both module and CLI interfaces
- JSON output format
- Configurable retry mechanism

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd web-scraper
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### As a Command-Line Tool

Basic usage:
```bash
python web_scraper.py https://example.com
```

With options:
```bash
python web_scraper.py https://example.com \
    --min-delay 2 \
    --max-delay 5 \
    --workers 4 \
    --output results.json \
    --log-dir logs
```

Available options:
- `--min-delay`: Minimum delay between requests (seconds)
- `--max-delay`: Maximum delay between requests (seconds)
- `--retries`: Maximum number of retry attempts
- `--workers`: Number of worker processes
- `--log-dir`: Directory to store log files
- `--output`: Output file path for scraped data (JSON)
- `--quiet`: Suppress progress bar

### As a Python Module

```python
from web_scraper import WebScraper

# Initialize the scraper
scraper = WebScraper(
    base_url="https://example.com",
    delay_range=(2, 5),
    max_retries=3,
    log_dir="logs"
)

# Start scraping
data, stats = scraper.scrape(show_progress=True)

# Process results
print(f"Scraped {stats['total_pages_scraped']} pages")
print(f"Processed {stats['total_urls_processed']} URLs")
```

## Output Format

The scraper outputs JSON data in the following format:
```json
{
    "data": {
        "url1": {
            "title": "Page Title",
            "text": "Page Content",
            "meta_description": "Meta Description"
        }
        // ... more URLs
    },
    "stats": {
        "total_pages_scraped": 10,
        "total_urls_processed": 12,
        "start_url": "https://example.com"
    }
}
```

## Logging

Logs are stored in the specified log directory (default: `logs/`). The log file contains detailed information about:
- Pages being processed
- Successful scrapes
- Failed attempts
- Progress updates
- Error messages

## Error Handling

- The scraper automatically retries failed requests
- 404 errors and other HTTP errors are logged but don't stop the scraping process
- Rate limiting and timeout issues are handled gracefully
- All errors are logged to the log file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

