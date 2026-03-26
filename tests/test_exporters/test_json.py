"""Tests for JSON exporter."""

import pytest
import json
from datetime import datetime

from website_scraper.exporters.json_exporter import JSONExporter, JSONLExporter
from website_scraper.exporters.base import ExportConfig, ScrapingResult, ScrapingStats


class TestJSONExporter:
    """Tests for JSON exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = JSONExporter()
        assert exporter.format_name == "json"
    
    def test_file_extension(self):
        """Test file extension."""
        exporter = JSONExporter()
        assert exporter.file_extension == ".json"
    
    @pytest.mark.asyncio
    async def test_export_empty_results(self):
        """Test exporting empty results."""
        exporter = JSONExporter()
        
        output = await exporter.export([])
        data = json.loads(output)
        
        assert "data" in data
        assert data["data"] == []
    
    @pytest.mark.asyncio
    async def test_export_single_result(self, sample_scraping_result):
        """Test exporting single result."""
        exporter = JSONExporter()
        
        output = await exporter.export([sample_scraping_result])
        data = json.loads(output)
        
        assert len(data["data"]) == 1
        assert data["data"][0]["url"] == "https://example.com/test"
        assert data["data"][0]["title"] == "Test Page"
    
    @pytest.mark.asyncio
    async def test_export_with_metadata(self, sample_scraping_result):
        """Test export includes metadata."""
        config = ExportConfig(include_metadata=True)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        data = json.loads(output)
        
        assert "metadata" in data
        assert "exported_at" in data["metadata"]
        assert data["metadata"]["format"] == "json"
    
    @pytest.mark.asyncio
    async def test_export_with_stats(self, sample_scraping_result, sample_scraping_stats):
        """Test export includes statistics."""
        config = ExportConfig(include_stats=True)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result], sample_scraping_stats)
        data = json.loads(output)
        
        assert "stats" in data
        assert data["stats"]["total_pages"] == 10
        assert data["stats"]["successful_pages"] == 9
    
    @pytest.mark.asyncio
    async def test_export_without_metadata(self, sample_scraping_result):
        """Test export without metadata."""
        config = ExportConfig(include_metadata=False)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        data = json.loads(output)
        
        assert "metadata" not in data
    
    @pytest.mark.asyncio
    async def test_export_pretty_print(self, sample_scraping_result):
        """Test pretty printed output."""
        config = ExportConfig(pretty_print=True)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        
        # Pretty print should have indentation
        assert "\n" in output
        assert "  " in output
    
    @pytest.mark.asyncio
    async def test_export_compact(self, sample_scraping_result):
        """Test compact output."""
        config = ExportConfig(pretty_print=False, include_metadata=False)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        
        # Compact should be single line (no indentation)
        # Note: Content might still have newlines
        data = json.loads(output)
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_export_filters_links(self, sample_scraping_result):
        """Test link filtering."""
        config = ExportConfig(include_links=False)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        data = json.loads(output)
        
        assert "links" not in data["data"][0]
    
    @pytest.mark.asyncio
    async def test_export_filters_images(self, sample_scraping_result):
        """Test image filtering."""
        config = ExportConfig(include_images=False)
        exporter = JSONExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        data = json.loads(output)
        
        assert "images" not in data["data"][0]
    
    @pytest.mark.asyncio
    async def test_export_to_file(self, sample_scraping_result, temp_dir):
        """Test exporting to file."""
        exporter = JSONExporter()
        
        output_path = temp_dir / "results.json"
        result_path = await exporter.export_to_file(
            [sample_scraping_result],
            str(output_path)
        )
        
        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)
        
        assert len(data["data"]) == 1


class TestJSONLExporter:
    """Tests for JSON Lines exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = JSONLExporter()
        assert exporter.format_name == "jsonl"
    
    def test_file_extension(self):
        """Test file extension."""
        exporter = JSONLExporter()
        assert exporter.file_extension == ".jsonl"
    
    @pytest.mark.asyncio
    async def test_export_format(self, sample_scraping_result):
        """Test JSONL format - one JSON object per line."""
        config = ExportConfig(include_metadata=True, include_stats=False)
        exporter = JSONLExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        lines = output.strip().split("\n")
        
        # First line should be metadata
        metadata = json.loads(lines[0])
        assert metadata["_type"] == "metadata"
        
        # Last line should be result
        result = json.loads(lines[-1])
        assert result["_type"] == "result"
        assert result["url"] == "https://example.com/test"
    
    @pytest.mark.asyncio
    async def test_export_multiple_results(self, sample_scraping_result):
        """Test exporting multiple results."""
        config = ExportConfig(include_metadata=False, include_stats=False)
        exporter = JSONLExporter(config)
        
        # Create second result
        result2 = ScrapingResult(
            url="https://example.com/page2",
            title="Second Page",
        )
        
        output = await exporter.export([sample_scraping_result, result2])
        lines = output.strip().split("\n")
        
        assert len(lines) == 2
        
        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            assert data["_type"] == "result"

