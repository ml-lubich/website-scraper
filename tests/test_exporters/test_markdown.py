"""Tests for Markdown exporter."""

import pytest

from website_scraper.exporters.markdown_exporter import (
    MarkdownExporter,
    SinglePageMarkdownExporter,
)
from website_scraper.exporters.base import ExportConfig, ScrapingResult, ScrapingStats


class TestMarkdownExporter:
    """Tests for Markdown exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = MarkdownExporter()
        assert exporter.format_name == "markdown"
    
    def test_file_extension(self):
        """Test file extension."""
        exporter = MarkdownExporter()
        assert exporter.file_extension == ".md"
    
    @pytest.mark.asyncio
    async def test_export_basic(self, sample_scraping_result):
        """Test basic markdown export."""
        exporter = MarkdownExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        # Check for main heading
        assert "# Web Scraping Results" in output
        
        # Check for page content
        assert "Test Page" in output
        assert "https://example.com/test" in output
    
    @pytest.mark.asyncio
    async def test_export_with_toc(self, sample_scraping_result):
        """Test export with table of contents."""
        config = ExportConfig(include_toc=True)
        exporter = MarkdownExporter(config)
        
        # Create multiple results
        result2 = ScrapingResult(
            url="https://example.com/page2",
            title="Second Page",
        )
        
        output = await exporter.export([sample_scraping_result, result2])
        
        assert "## Table of Contents" in output
    
    @pytest.mark.asyncio
    async def test_export_with_stats(self, sample_scraping_result, sample_scraping_stats):
        """Test export with statistics."""
        config = ExportConfig(include_stats=True)
        exporter = MarkdownExporter(config)
        
        output = await exporter.export([sample_scraping_result], sample_scraping_stats)
        
        assert "## Scraping Statistics" in output
        assert "Total Pages" in output
        assert "10" in output  # total_pages
    
    @pytest.mark.asyncio
    async def test_export_preserves_headings(self, sample_scraping_result):
        """Test that headings are preserved."""
        exporter = MarkdownExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        # Check headings section
        assert "### Page Headings" in output or "Main Heading" in output
    
    @pytest.mark.asyncio
    async def test_export_includes_links(self, sample_scraping_result):
        """Test that links are included."""
        config = ExportConfig(include_links=True)
        exporter = MarkdownExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        
        # Links should be in markdown format
        assert "### Links Found" in output
        assert "[" in output  # Markdown link syntax
    
    @pytest.mark.asyncio
    async def test_export_metadata_section(self, sample_scraping_result):
        """Test metadata section."""
        config = ExportConfig(include_metadata=True)
        exporter = MarkdownExporter(config)
        
        output = await exporter.export([sample_scraping_result])
        
        assert "## Export Information" in output
        assert "Exported at:" in output
    
    @pytest.mark.asyncio
    async def test_export_to_file(self, sample_scraping_result, temp_dir):
        """Test exporting to file."""
        exporter = MarkdownExporter()
        
        output_path = temp_dir / "results.md"
        result_path = await exporter.export_to_file(
            [sample_scraping_result],
            str(output_path)
        )
        
        assert output_path.exists()
        
        content = output_path.read_text()
        assert "# Web Scraping Results" in content


class TestSinglePageMarkdownExporter:
    """Tests for single page Markdown exporter."""
    
    def test_format_name(self):
        """Test format name."""
        exporter = SinglePageMarkdownExporter()
        assert exporter.format_name == "markdown-single"
    
    @pytest.mark.asyncio
    async def test_export_single_page(self, sample_scraping_result):
        """Test single page export."""
        exporter = SinglePageMarkdownExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        # Should have title as main heading
        assert "# Test Page" in output
        
        # Should have source link
        assert "Source:" in output
        assert "https://example.com/test" in output
    
    @pytest.mark.asyncio
    async def test_export_empty_results(self):
        """Test export with no results."""
        exporter = SinglePageMarkdownExporter()
        
        output = await exporter.export([])
        
        assert "# No Results" in output
    
    @pytest.mark.asyncio
    async def test_export_with_summary(self, sample_scraping_result):
        """Test export includes summary."""
        exporter = SinglePageMarkdownExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        if sample_scraping_result.summary:
            assert "## Summary" in output
            assert sample_scraping_result.summary in output
    
    @pytest.mark.asyncio
    async def test_export_with_topics(self, sample_scraping_result):
        """Test export includes topics."""
        exporter = SinglePageMarkdownExporter()
        
        output = await exporter.export([sample_scraping_result])
        
        if sample_scraping_result.topics:
            assert "Topics:" in output

