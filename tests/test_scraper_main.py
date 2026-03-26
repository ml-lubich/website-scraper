"""Exercise ``website_scraper.scraper.main`` with heavy mocking."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import website_scraper.scraper as scraper_mod


def test_scraper_module_main_writes_output(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    out = tmp_path / "out.json"
    fake = MagicMock()
    fake.scrape.return_value = (
        {"https://example.com": {"title": "T"}},
        {
            "start_url": "https://example.com",
            "total_pages_scraped": 1,
            "total_urls_processed": 1,
            "failed_urls": 0,
            "success_rate": "100%",
            "duration": "1 seconds",
        },
    )
    fake.logger = MagicMock()

    argv = [
        "scraper",
        "https://example.com",
        "-l",
        str(log_dir),
        "-o",
        str(out),
        "-q",
    ]

    with patch.object(scraper_mod, "WebScraper", return_value=fake):
        with patch.object(scraper_mod, "freeze_support"):
            with patch.object(sys, "argv", argv):
                scraper_mod.main()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "data" in payload and "stats" in payload
