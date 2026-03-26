"""Cover JSONExporter.export_streaming (uses aiofiles)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from website_scraper.exporters.base import ExportConfig, ScrapingResult, ScrapingStats
from website_scraper.exporters.json_exporter import JSONExporter


@pytest.mark.asyncio
async def test_json_export_streaming_writes_file(tmp_path) -> None:
    out = tmp_path / "big.json"
    exporter = JSONExporter(ExportConfig(include_metadata=True, include_stats=True))
    results = [
        ScrapingResult(url="https://example.com/a", title="A", content="hello"),
    ]
    stats = ScrapingStats(
        total_pages=1,
        successful_pages=1,
        start_url="https://example.com/",
        domain="example.com",
    )

    fake_file = AsyncMock()
    fake_cm = MagicMock()
    fake_cm.__aenter__ = AsyncMock(return_value=fake_file)
    fake_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("aiofiles.open", return_value=fake_cm):
        path = await exporter.export_streaming(results, str(out), stats)

    assert path == str(out)
    assert fake_file.write.await_count >= 3
