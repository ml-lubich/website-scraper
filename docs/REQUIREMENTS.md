# Requirements

## Product goals

- Scrape pages under a base URL with configurable depth/link following (see implementation in `website_scraper/scraper.py`).
- Reduce obvious bot patterns: random delays, rotating user agents, optional SSL verification control.
- Scale via **multiprocessing** where configured.
- Ship as an installable package with a **CLI** entrypoint (`website-scraper`).

## Technical constraints

- **Python:** `>=3.7` per `setup.py` (`python_requires`).
- **Dependencies:** `requests`, `beautifulsoup4`, `fake-useragent`, `tqdm`, `lxml` (see `install_requires` in `setup.py`).
- **Optional:** `undetected-chromedriver` via extra `pip install "website-scraper[undetected]"`; host must have a compatible **Chrome** installation.

## Non-goals

- Guaranteeing bypass of every anti-bot system (network reputation and site policy still apply).
