# Design

## CLI

`website-scraper` accepts a base URL, delay ranges, retries, worker count, log directory, optional output path, quiet mode, optional SSL verification disable, and optional **`--undetected-chrome`** / **`--uc-headed`** for Chrome-based fetching. It instantiates `WebScraper` with matching parameters and prints JSON (or writes to `-o`).

See `website_scraper/cli.py` and the README for the full option list.

## Library usage

Import `WebScraper` from `website_scraper`, construct with `base_url` and keyword options matching the scraper implementation, call `scrape()`.

Relevant constructor flags for browser mode: `use_undetected_chrome`, `uc_headless`, `uc_page_load_timeout`, `uc_browser_executable_path`. Install optional extra: `pip install "website-scraper[undetected]"`.

## Logging and politeness

Logging is configured under the user-chosen log directory. Delays are randomized between min/max bounds to spread requests over time (and between undetected Chrome navigations when that mode is enabled).
