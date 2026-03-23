# API

## Public Python surface

`website_scraper/__init__.py` exports:

- **`WebScraper`** — main class (defined in `website_scraper/scraper.py`).
- **`__version__`** — package version string.

Prefer importing from the package root:

```python
from website_scraper import WebScraper
```

## CLI

- **Command:** `website-scraper`
- **Entry point:** `website_scraper.cli:main` (see `setup.py` `entry_points`).

## `WebScraper` constructor (excerpt)

Besides URL, delays, retries, logging, `max_workers`, and `verify_ssl`, the scraper supports:

- **`use_undetected_chrome`** — use undetected-chromedriver instead of `requests` (requires optional dependency).
- **`uc_headless`** — headless Chrome when using undetected mode (default `True`).
- **`uc_page_load_timeout`** — seconds passed to the WebDriver page-load timeout.
- **`uc_browser_executable_path`** — optional path to the Chrome/Chromium binary.

`scrape()` returns `(data, stats)`; `stats` includes **`fetch_mode`**: `"requests"` or `"undetected_chrome"`.

## Internals

Other names in `scraper.py` (helpers, `main`, etc.) are implementation details unless promoted in `__init__.py` and documented here.
