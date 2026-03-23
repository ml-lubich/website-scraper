# Overview

**website-scraper** is a Python library and CLI for crawling websites using **BeautifulSoup** for parsing. By default it fetches with **requests** and optional **multiprocessing**. Optionally it can fetch with **undetected-chromedriver** (real Chrome) for tougher sites or script-heavy pages. It focuses on polite delays, rotating user agents (HTTP mode), logging, and JSON-oriented output.

## Distribution

- **PyPI package name:** `website-scraper` (`pip install website-scraper`)
- **Import name:** `website_scraper`
- **CLI command:** `website-scraper`
- **Version:** see `website_scraper/__init__.py` and `setup.py` (should stay aligned for releases).

Packaging is **setuptools** via `setup.py` (root of the repository).

## Where to read next

| Doc | Purpose |
|-----|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Goals and constraints |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layout and main components |
| [DESIGN.md](DESIGN.md) | CLI and `WebScraper` behavior |
| [API.md](API.md) | Public surface |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Install and publishing notes |
| [TESTING.md](TESTING.md) | How tests are run |

The repository **README** is the primary user-facing guide. **Release history:** [GitHub releases](https://github.com/ml-lubich/website-scraper/releases) and commit history.
