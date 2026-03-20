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

## Internals

Other names in `scraper.py` (helpers, `main`, etc.) are implementation details unless promoted in `__init__.py` and documented here.
