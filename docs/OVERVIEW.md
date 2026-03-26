# Overview

**website-scraper** is a Python library and CLI for crawling websites using **BeautifulSoup** for parsing. By default it fetches with **requests** and optional **multiprocessing**. For sites that need a real browser, use **undetected-chromedriver** (`pip install "website-scraper[undetected]"` + **Google Chrome** on the machine): set `use_undetected_chrome=True` or CLI `--undetected-chrome` / `--uc-headed`. That path drives **Chrome** in headless or headed mode with the undetected driver stack (single process; not combined with the multiprocessing HTTP pool).

## Distribution

- **PyPI package name:** `website-scraper` (`pip install website-scraper`)
- **Import name:** `website_scraper`
- **CLI command:** `website-scraper`
- **Version:** see `website_scraper/__init__.py` and `setup.py` (should stay aligned for releases).

Packaging is **setuptools** via `setup.py` (root of the repository).

## Canonical documentation (five files)

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layout and main components |
| [DESIGN.md](DESIGN.md) | Requirements, CLI, and `WebScraper` behavior (including undetected Chrome) |
| [API.md](API.md) | Public surface |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Install, publishing, and testing |

The repository **README** is the quick-start guide. Release notes: [GitHub releases](https://github.com/ml-lubich/website-scraper/releases).

## Archive

Historical code under `archive/` is **not** part of the installable `website_scraper` API.

| Path | Note |
|------|------|
| `archive/ml_ms_2020/` | 2020 “Machine-Learning-MS” / Reddit-era snapshot. Some scripts target Python 2 or missing modules; not wired into the current package. For a maintained Python 3 demo, see `examples/reddit_berkeley_preview.py`. |
