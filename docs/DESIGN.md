# Design

## CLI

`website-scraper` accepts a base URL, delay ranges, retries, worker count, log directory, optional output path, quiet mode, and optional SSL verification disable. It instantiates `WebScraper` with matching parameters and prints JSON (or writes to `-o`).

See `website_scraper/cli.py` and the README for the full option list.

## Library usage

Import `WebScraper` from `website_scraper`, construct with `base_url` and keyword options matching the scraper implementation, call `scrape()`.

## Logging and politeness

Logging is configured under the user-chosen log directory. Delays are randomized between min/max bounds to spread requests over time.
