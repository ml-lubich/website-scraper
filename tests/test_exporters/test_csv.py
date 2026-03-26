"""Tests for CSV exporter."""

import pytest
import csv
from io import StringIO

from website_scraper.exporters.csv_exporter import (
    CSVExporter,
    TSVExporter,
    FlatCSVExporter,
)
from website_scraper.exporters.base import ExportConfig, ScrapingResult, ScrapingStats


class TestCSVExporter:
    """Tests for CSV exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = CSVExporter()
        assert exporter.format_name == "csv"
    
    def test_file_extension(self):
        """Test file extension."""
        exporter = CSVExporter()
        assert exporter.file_extension == ".csv"
    
    def test_default_columns(self):
        """Test default columns are set."""
        exporter = CSVExporter()
        
        assert "url" in exporter.columns
        assert "title" in exporter.columns
        assert "content" in exporter.columns
    
    def test_custom_columns(self):
        """Test custom columns."""
        exporter = CSVExporter(columns=["url", "title"])
        
        assert exporter.columns == ["url", "title"]
    
    @pytest.mark.asyncio
    async def test_export_basic(self, sample_scraping_result):
        """Test basic CSV export."""
        exporter = CSVExporter(columns=["url", "title"])
        
        output = await exporter.export([sample_scraping_result])
        
        # Parse CSV
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        # Check header
        assert rows[0] == ["url", "title"]
        
        # Check data
        assert rows[1][0] == "https://example.com/test"
        assert rows[1][1] == "Test Page"
    
    @pytest.mark.asyncio
    async def test_export_multiple_results(self, sample_scraping_result):
        """Test exporting multiple results."""
        exporter = CSVExporter(columns=["url", "title"])
        
        result2 = ScrapingResult(
            url="https://example.com/page2",
            title="Page Two",
        )
        
        output = await exporter.export([sample_scraping_result, result2])
        
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        assert len(rows) == 3  # Header + 2 data rows
    
    @pytest.mark.asyncio
    async def test_export_handles_lists(self, sample_scraping_result):
        """Test exporting handles list values."""
        exporter = CSVExporter(columns=["url", "topics"])
        
        output = await exporter.export([sample_scraping_result])
        
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        # Topics should be joined with semicolons
        assert "testing" in rows[1][1]
        assert "example" in rows[1][1]
    
    @pytest.mark.asyncio
    async def test_export_handles_none(self):
        """Test exporting handles None values."""
        result = ScrapingResult(
            url="https://example.com",
            title="Test",
            meta_description=None,
        )
        
        exporter = CSVExporter(columns=["url", "meta_description"])
        
        output = await exporter.export([result])
        
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        assert rows[1][1] == ""  # None should be empty string
    
    @pytest.mark.asyncio
    async def test_export_truncates_content(self, sample_scraping_result):
        """Test content truncation."""
        config = ExportConfig(max_content_length=10)
        exporter = CSVExporter(config, columns=["url", "content"])
        
        output = await exporter.export([sample_scraping_result])
        
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        assert len(rows[1][1]) <= 10
    
    @pytest.mark.asyncio
    async def test_export_to_file(self, sample_scraping_result, temp_dir):
        """Test exporting to file."""
        exporter = CSVExporter()
        
        output_path = temp_dir / "results.csv"
        await exporter.export_to_file(
            [sample_scraping_result],
            str(output_path)
        )
        
        assert output_path.exists()


class TestTSVExporter:
    """Tests for TSV exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = TSVExporter()
        assert exporter.format_name == "tsv"
    
    def test_file_extension(self):
        """Test file extension."""
        exporter = TSVExporter()
        assert exporter.file_extension == ".tsv"
    
    def test_delimiter_is_tab(self):
        """Test delimiter is tab."""
        exporter = TSVExporter()
        assert exporter.config.csv_delimiter == "\t"
    
    @pytest.mark.asyncio
    async def test_export_uses_tabs(self, sample_scraping_result):
        """Test export uses tab delimiter."""
        exporter = TSVExporter(columns=["url", "title"])
        
        output = await exporter.export([sample_scraping_result])
        
        # Should contain tabs
        assert "\t" in output


class TestFlatCSVExporter:
    """Tests for flat CSV exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = FlatCSVExporter()
        assert exporter.format_name == "csv-flat"
    
    @pytest.mark.asyncio
    async def test_export_discovers_columns(self, sample_scraping_result):
        """Test auto-discovery of columns."""
        exporter = FlatCSVExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        # Header should have auto-discovered columns
        assert "url" in rows[0]
        assert "title" in rows[0]
    
    @pytest.mark.asyncio
    async def test_export_flattens_nested(self, sample_scraping_result):
        """Test flattening of nested data."""
        exporter = FlatCSVExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        reader = csv.reader(StringIO(output))
        rows = list(reader)
        
        # Should have flattened nested structures
        # Links count instead of full link data
        assert any("links_count" in col for col in rows[0]) or any("links" in col for col in rows[0])
    
    @pytest.mark.asyncio
    async def test_flatten_dict(self):
        """Test dictionary flattening helper."""
        exporter = FlatCSVExporter()
        
        nested = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3,
            },
            "e": [1, 2, 3],
        }
        
        flat = exporter._flatten_dict(nested)
        
        assert flat["a"] == 1
        assert flat["b_c"] == 2
        assert flat["b_d"] == 3
        assert "1" in flat["e"]  # List should be joined

