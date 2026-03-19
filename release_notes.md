## 0.1.2

- Reorganize repo: `archive/ml_ms_2020/` for the 2020 ML/Berkeley snapshot (not shipped as importable package code).
- Add `examples/reddit_berkeley_preview.py` (Python 3) as an optional demo aligned with the main stack.
- Fix README fenced code block in the package usage section.

Initial release of website-scraper

Features:
- Multiprocessing support for faster scraping
- Rate limiting and random delays for bot detection avoidance
- Rotating User-Agents and browser fingerprints
- Comprehensive logging system with debug and info levels
- Progress tracking with progress bar
- XML content detection and proper handling
- SSL verification options
- Command-line interface with short and long options
- Python package with easy-to-use API

## Installation
```bash
pip install website-scraper
```

## Usage
```bash
website-scraper https://example.com -o results.json
``` 