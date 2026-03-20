# Architecture

## Components

1. **`website_scraper/scraper.py`** — `WebScraper`: HTTP fetch via `requests`, HTML parse via BeautifulSoup, crawl state, optional `ProcessPoolExecutor` for parallel work, progress via `tqdm`.
2. **`website_scraper/cli.py`** — Argument parsing, constructs `WebScraper`, writes JSON to stdout or `-o` file.
3. **`archive/`** — Historical or alternate implementations; **not** part of the installable API (see README repository layout).

## Data flow (high level)

CLI or library code builds `WebScraper` → `scrape()` fetches and parses pages → structured `data` and `stats` dicts → JSON serialization for CLI output.

## Extension points

Behavior changes belong in `WebScraper` and related helpers inside `scraper.py` unless a new module is introduced deliberately and documented here and in [API.md](API.md).
