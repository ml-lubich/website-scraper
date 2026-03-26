"""Extra coverage for undetected-chromedriver paths in WebScraper."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from website_scraper import WebScraper, scrape_url


def test_scrape_url_delegates_to_web_scraper(tmp_path) -> None:
    with patch.object(WebScraper, "scrape", return_value=({}, {"fetch_mode": "requests"})) as mock_scrape:
        data, stats = scrape_url("https://example.com/", show_progress=False, log_dir=str(tmp_path))
    mock_scrape.assert_called_once_with(show_progress=False)
    assert stats.get("fetch_mode") == "requests"


def test_uc_load_page_retries_then_succeeds(tmp_path) -> None:
    mock_driver = MagicMock()
    mock_driver.page_source = "<html><title>OK</title></html>"
    calls = {"n": 0}

    def flaky_get(url: str) -> None:
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")

    mock_driver.get = MagicMock(side_effect=flaky_get)

    fake = types.ModuleType("undetected_chromedriver")
    fake.ChromeOptions = MagicMock(return_value=MagicMock())
    fake.Chrome = MagicMock(return_value=mock_driver)

    with patch(
        "website_scraper.scraper.importlib.util.find_spec",
        return_value=MagicMock(),
    ):
        sys.modules["undetected_chromedriver"] = fake
        try:
            s = WebScraper(
                "https://example.com",
                log_dir=str(tmp_path),
                use_undetected_chrome=True,
                max_retries=3,
            )
            html = s._uc_load_page(mock_driver, "https://example.com/a")
        finally:
            sys.modules.pop("undetected_chromedriver", None)

    assert html is not None
    assert calls["n"] == 2


def test_process_url_uc_xml_content(tmp_path) -> None:
    xml = '<?xml version="1.0"?><root><item>a</item></root>'
    mock_driver = MagicMock()
    mock_driver.page_source = xml

    fake = types.ModuleType("undetected_chromedriver")
    fake.ChromeOptions = MagicMock(return_value=MagicMock())
    fake.Chrome = MagicMock(return_value=mock_driver)

    with patch(
        "website_scraper.scraper.importlib.util.find_spec",
        return_value=MagicMock(),
    ):
        sys.modules["undetected_chromedriver"] = fake
        try:
            s = WebScraper(
                "https://example.com",
                log_dir=str(tmp_path),
                use_undetected_chrome=True,
            )
            url, data, links = s._process_url_uc(mock_driver, "https://example.com/data.xml")
        finally:
            sys.modules.pop("undetected_chromedriver", None)

    assert data is not None
    assert url.endswith(".xml")


def test_create_uc_driver_options(tmp_path) -> None:
    fake_opts = MagicMock()
    fake = types.ModuleType("undetected_chromedriver")
    fake.ChromeOptions = MagicMock(return_value=fake_opts)
    mock_driver = MagicMock()
    fake.Chrome = MagicMock(return_value=mock_driver)

    with patch(
        "website_scraper.scraper.importlib.util.find_spec",
        return_value=MagicMock(),
    ):
        sys.modules["undetected_chromedriver"] = fake
        try:
            s = WebScraper(
                "https://example.com",
                log_dir=str(tmp_path),
                use_undetected_chrome=True,
                uc_headless=False,
                verify_ssl=False,
                uc_browser_executable_path="/fake/chrome",
                uc_page_load_timeout=12,
            )
            s._create_uc_driver()
        finally:
            sys.modules.pop("undetected_chromedriver", None)

    mock_driver.set_page_load_timeout.assert_called_once_with(12)
    fake.Chrome.assert_called_once()
    call_kw = fake.Chrome.call_args.kwargs
    assert call_kw.get("use_subprocess") is False
