# Testing

## Runner

- **Framework:** pytest (see repository `tests/` and any CI configuration).
- **Layout:** `tests/` with `test_*.py` modules.

## Commands

```bash
pytest
```

Use a virtual environment with dev dependencies if your workflow installs them (e.g. `pytest` via `pip install -e ".[dev]"` if defined).

## Expectations

Tests should exercise real package imports and core `WebScraper` / CLI behavior where practical. Prefer minimal mocking for HTTP only when network isolation is required; follow patterns already used in `tests/`.
