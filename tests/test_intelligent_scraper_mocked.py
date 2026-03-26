"""Unit tests for IntelligentScraper with Playwright mocked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from website_scraper.intelligent_scraper import IntelligentScraper, ScraperConfig


LONG_HTML = """<!DOCTYPE html>
<html><head><title>Demo</title></head><body>
<article class="post"><p>""" + ("x" * 200) + """</p>
<a href="/next">Next</a>
</article></body></html>"""


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    d = tmp_path / "logs"
    d.mkdir()
    return d


@pytest.mark.asyncio
async def test_intelligent_scraper_scrape_one_page(temp_log_dir: Path) -> None:
    mock_page = MagicMock()
    mock_page.close = AsyncMock()

    mock_response = MagicMock()
    mock_response.status = 200

    mock_driver = MagicMock()
    mock_driver.__aenter__ = AsyncMock(return_value=mock_driver)
    mock_driver.__aexit__ = AsyncMock(return_value=None)
    mock_driver.new_page = AsyncMock(return_value=mock_page)
    mock_driver.goto = AsyncMock(return_value=mock_response)
    mock_driver.get_page_content = AsyncMock(return_value=LONG_HTML)

    with patch(
        "website_scraper.intelligent_scraper.PlaywrightDriver",
        return_value=mock_driver,
    ):
        config = ScraperConfig(
            base_url="https://example.com/start",
            log_dir=str(temp_log_dir),
            max_pages=5,
            max_depth=2,
            use_browser=True,
            use_llm=False,
        )
        scraper = IntelligentScraper(config)
        out = await scraper.scrape()

    assert "data" in out and "stats" in out
    assert out["stats"]["start_url"] == "https://example.com/start"
    assert out["stats"]["total_urls_visited"] >= 1


@pytest.mark.asyncio
async def test_intelligent_scraper_export_roundtrip(temp_log_dir: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "out.json"
    mock_page = MagicMock()
    mock_page.close = AsyncMock()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_driver = MagicMock()
    mock_driver.__aenter__ = AsyncMock(return_value=mock_driver)
    mock_driver.__aexit__ = AsyncMock(return_value=None)
    mock_driver.new_page = AsyncMock(return_value=mock_page)
    mock_driver.goto = AsyncMock(return_value=mock_response)
    mock_driver.get_page_content = AsyncMock(return_value=LONG_HTML)

    with patch(
        "website_scraper.intelligent_scraper.PlaywrightDriver",
        return_value=mock_driver,
    ):
        config = ScraperConfig(
            base_url="https://example.com/",
            log_dir=str(temp_log_dir),
            max_pages=2,
            export_format="json",
            output_path=str(out_path),
            use_browser=True,
            use_llm=False,
        )
        scraper = IntelligentScraper(config)
        path = await scraper.scrape_and_export()

    assert path.exists()


def test_format_duration_and_delay(temp_log_dir: Path) -> None:
    config = ScraperConfig(
        base_url="https://example.com/",
        log_dir=str(temp_log_dir),
        use_browser=False,
    )
    scraper = IntelligentScraper(config)
    assert scraper._format_duration(30.0).endswith("seconds")
    assert scraper._format_duration(120.0).endswith("minutes")
    assert scraper._format_duration(4000.0).endswith("hours")
    d = scraper._get_random_delay()
    assert config.delay_range[0] <= d <= config.delay_range[1]
