# Deployment

## End users (PyPI)

```bash
pip install website-scraper
```

## Development install

From a clone:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
pip install -e ".[undetected]"   # optional: Chrome-backed fetching for local testing
```

## Publishing (maintainers)

This repository uses **`setup.py`** with setuptools. Typical workflow: bump version in `setup.py` and `website_scraper/__init__.py`, tag, build sdist/wheel, upload with Twine. Align with your org’s release checklist.

## Documentation link

Project URL in `setup.py` points at the GitHub repository; canonical spec lives under `docs/` (start with [OVERVIEW.md](OVERVIEW.md)).
