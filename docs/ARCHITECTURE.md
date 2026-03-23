# Architecture

## Components

1. **`website_scraper/scraper.py`** — `WebScraper`: HTML parse via BeautifulSoup and shared link/data extraction. **Default fetch:** `requests` + optional `ProcessPoolExecutor` for parallel workers. **Optional fetch:** one [undetected-chromedriver](https://pypi.org/project/undetected-chromedriver/) Chrome instance (`use_undetected_chrome=True`) — **single-process only** (no worker pool). Progress via `tqdm`.
2. **`website_scraper/cli.py`** — Argument parsing, constructs `WebScraper`, writes JSON to stdout or `-o` file.
3. **`archive/`** — Historical or alternate implementations; **not** part of the installable API (see README repository layout).

## Data flow (high level)

CLI or library code builds `WebScraper` → `scrape()` fetches and parses pages → structured `data` and `stats` dicts → JSON serialization for CLI output.

## Extension points

Behavior changes belong in `WebScraper` and related helpers inside `scraper.py` unless a new module is introduced deliberately and documented here and in [API.md](API.md).
