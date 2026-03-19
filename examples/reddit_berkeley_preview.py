#!/usr/bin/env python3
"""
Optional demo: fetch Reddit HTML for r/berkeley and print a short preview.
Uses the same stack as the main package (requests + BeautifulSoup).

This is not the multiprocessing site crawler; it mirrors the spirit of the
2020 `archive/ml_ms_2020/webscraper.py` in Python 3.

Usage (from repo root):
  python examples/reddit_berkeley_preview.py
"""

from __future__ import annotations

import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup


def fetch_preview(url: str, max_chars: int = 2000) -> Optional[str]:
    headers = {
        "User-Agent": "website-scraper-examples/1.0 (educational preview; +https://github.com/ml-lubich/website-scraper)",
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    if not text:
        return "(no text extracted; page may require JavaScript)"
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


def main() -> None:
    url = "https://www.reddit.com/r/berkeley/"
    preview = fetch_preview(url)
    if preview is None:
        sys.exit(1)
    print(preview)


if __name__ == "__main__":
    main()
