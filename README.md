# Website Scraper

A robust, multiprocessing-enabled web scraper that can be used both as a module and as a command-line tool. Features include rate limiting, bot detection avoidance, and comprehensive logging.

## Features

- Multiprocessing support for faster scraping
- Rate limiting and random delays to avoid detection
- Rotating User-Agents and browser fingerprints
- Comprehensive logging system with separate debug and info logs
- Progress tracking with progress bar
- Both module and CLI interfaces
- JSON output format
- Configurable retry mechanism
- XML content detection and proper handling
- SSL verification options

## Installation

### From Source
1. Clone the repository:
   ```bash
   git clone git@github.com:ml-lubich/website-scraper.git
   cd website-scraper
   ```

2. Install the package:
   ```bash
   pip install .
   ```

### From PyPI (coming soon)
```bash
pip install website-scraper
```

## Usage

### As a Command-Line Tool

The package installs a `website-scraper` command that can be used directly:

Basic usage:
```bash
website-scraper https://example.com
```

With options (long form):
```bash
website-scraper https://example.com \
    --min-delay 2 \
    --max-delay 5 \
    --workers 4 \
    --output results.json \
    --log-dir logs \
    --no-verify-ssl
```

With options (short form):
```bash
website-scraper https://example.com \
    -m 2 \
    -M 5 \
    -w 4 \
    -o results.json \
    -l logs \
    -k
```

Available options:
- `-m, --min-delay`: Minimum delay between requests (seconds)
- `-M, --max-delay`: Maximum delay between requests (seconds)
- `-r, --retries`: Maximum number of retry attempts
- `-w, --workers`: Number of worker processes
- `-l, --log-dir`: Directory to store log files
- `-o, --output`: Output file path for scraped data (JSON)
- `-q, --quiet`: Suppress progress bar
- `-k, --no-verify-ssl`: Disable SSL certificate verification (use with caution)

### Output Handling

The scraper can handle output in two ways:
1. Write to a file (when `-o` or `--output` is specified)
2. Print to stdout (when no output file is specified)

This allows for flexible usage:
```bash
# Write to file
website-scraper example.com -o results.json

# Pipe to another command
website-scraper example.com | jq .

# Save output using shell redirection
website-scraper example.com > results.json
```

### As a Python Package

```python
from website_scraper import WebScraper

# Initialize the scraper
scraper = WebScraper(
    base_url="https://example.com",
    delay_range=(2, 5),
    max_retries=3,
    log_dir="logs",
    verify_ssl=True  # Set to False to disable SSL verification
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
        "failed_urls": 2,
        "start_url": "https://example.com",
        "duration": "5 minutes",
        "success_rate": "83.3%"
    }
}
```

## Development

1. Clone the repository:
   ```bash
   git clone git@github.com:ml-lubich/website-scraper.git
   cd website-scraper
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

## Logging

Logs are stored in the specified log directory (default: `logs/`). Two types of log files are generated:
- `[timestamp].log`: Contains INFO level and above messages
- `debug_[timestamp].log`: Contains detailed DEBUG level messages

The logs include:
- Request attempts and responses
- Pages being processed
- Successful scrapes
- Failed attempts
- Progress updates
- Error messages
- Content type detection
- Parser selection

## Error Handling

- Automatic retry mechanism for failed requests
- Graceful handling of SSL certificate issues
- Proper handling of XML vs HTML content
- Rate limiting and timeout handling
- Comprehensive error logging
- All errors are logged but don't stop the scraping process

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

