"""Smoke tests for the synchronous CLI (website_scraper.cli)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import website_scraper.cli as cli_mod


def test_cli_main_writes_json_to_stdout(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    fake_scraper = MagicMock()
    fake_scraper.scrape.return_value = (
        {"https://example.com": {"title": "T"}},
        {"fetch_mode": "requests", "total_pages_scraped": 1},
    )
    fake_scraper.logger = MagicMock()

    argv = [
        "website-scraper",
        "https://example.com",
        "-l",
        str(log_dir),
        "-q",
    ]

    with patch.object(cli_mod, "WebScraper", return_value=fake_scraper):
        with patch.object(sys, "argv", argv):
            with patch("website_scraper.cli.subprocess.check_call"):
                cli_mod.main()

    fake_scraper.scrape.assert_called_once_with(show_progress=False)


def test_cli_main_with_output_file(tmp_path: Path) -> None:
    out = tmp_path / "data.json"
    log_dir = tmp_path / "logs"
    fake_scraper = MagicMock()
    fake_scraper.scrape.return_value = ({}, {"ok": True})
    fake_scraper.logger = MagicMock()

    argv = [
        "website-scraper",
        "https://example.com",
        "-l",
        str(log_dir),
        "-o",
        str(out),
        "-q",
    ]

    with patch.object(cli_mod, "WebScraper", return_value=fake_scraper):
        with patch.object(sys, "argv", argv):
            with patch("website_scraper.cli.subprocess.check_call"):
                cli_mod.main()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "data" in payload and "stats" in payload


def test_cli_main_exits_on_error(tmp_path: Path) -> None:
    argv = ["website-scraper", "https://example.com", "-l", str(tmp_path / "logs")]

    with patch.object(cli_mod, "WebScraper", side_effect=RuntimeError("boom")):
        with patch.object(sys, "argv", argv):
            with pytest.raises(SystemExit) as exc:
                cli_mod.main()
            assert exc.value.code == 1
