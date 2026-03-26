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

## Testing

- **Framework:** pytest (async tests use `pytest-asyncio` with `asyncio_mode = auto`; see `pytest.ini`).
- **Layout:** `tests/` — `collect_ignore` in `tests/conftest.py` skips legacy files that target an older CLI / mismatched APIs until realigned.
- **Coverage:** `.coveragerc` omits optional LLM *provider implementation* modules that need vendor SDKs and network; factory and base types stay measured. Target **≥ 80%** (enforced in `pytest.ini`).
- **Undetected Chrome in tests:** `tests/test_scraper.py` and `tests/test_undetected_chrome_extra.py` mock `undetected_chromedriver` so CI does not need Chrome installed.

Local install (matches CI intent):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
pip install -e ".[dev,undetected]"
```

Run tests:

```bash
python -m pytest tests/
```

With coverage report:

```bash
python -m pytest tests/ --cov=website_scraper --cov-report=term-missing
```
