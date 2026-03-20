# Testing

## Runner

- **Framework:** pytest.
- **Layout:** `tests/` (currently `tests/test_scraper.py`).

## Install (local)

Matches CI (see `.github/workflows/test.yml`):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements-dev.txt
pip install -e .
```

Or equivalently:

```bash
pip install -e ".[dev]"
```

## Commands

```bash
python -m pytest tests/ -v
```

Optional coverage:

```bash
python -m pytest tests/ --cov=website_scraper --cov-report=term-missing
```

## Expectations

`TestWebScraper` uses **`unittest`**-style tests run by pytest; HTTP is **mocked** via `unittest.mock.patch` on `requests.Session` where network I/O must be avoided. Link and data extraction tests use real BeautifulSoup parsing on fixture HTML (no network).
