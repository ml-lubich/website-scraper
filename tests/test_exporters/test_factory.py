"""Tests for exporter factory."""

import pytest

from website_scraper.exporters.factory import (
    create_exporter,
    get_exporter_for_extension,
    ExporterType,
)
from website_scraper.exporters.json_exporter import JSONExporter, JSONLExporter
from website_scraper.exporters.markdown_exporter import MarkdownExporter
from website_scraper.exporters.csv_exporter import CSVExporter, TSVExporter


class TestCreateExporter:
    """Tests for create_exporter function."""
    
    def test_create_json_exporter(self):
        """Test creating JSON exporter."""
        exporter = create_exporter(ExporterType.JSON)
        
        assert isinstance(exporter, JSONExporter)
    
    def test_create_jsonl_exporter(self):
        """Test creating JSONL exporter."""
        exporter = create_exporter(ExporterType.JSONL)
        
        assert isinstance(exporter, JSONLExporter)
    
    def test_create_markdown_exporter(self):
        """Test creating Markdown exporter."""
        exporter = create_exporter(ExporterType.MARKDOWN)
        
        assert isinstance(exporter, MarkdownExporter)
    
    def test_create_csv_exporter(self):
        """Test creating CSV exporter."""
        exporter = create_exporter(ExporterType.CSV)
        
        assert isinstance(exporter, CSVExporter)
    
    def test_create_tsv_exporter(self):
        """Test creating TSV exporter."""
        exporter = create_exporter(ExporterType.TSV)
        
        assert isinstance(exporter, TSVExporter)
    
    def test_create_with_string_type(self):
        """Test creating with string type."""
        exporter = create_exporter("json")
        
        assert isinstance(exporter, JSONExporter)
    
    def test_create_with_string_case_insensitive(self):
        """Test string type is case insensitive."""
        exporter = create_exporter("JSON")
        
        assert isinstance(exporter, JSONExporter)
    
    def test_create_with_invalid_type_raises(self):
        """Test invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown exporter type"):
            create_exporter("invalid_type")


class TestGetExporterForExtension:
    """Tests for get_exporter_for_extension function."""
    
    def test_json_extension(self):
        """Test .json extension."""
        result = get_exporter_for_extension(".json")
        assert result == ExporterType.JSON
    
    def test_json_without_dot(self):
        """Test json without leading dot."""
        result = get_exporter_for_extension("json")
        assert result == ExporterType.JSON
    
    def test_jsonl_extension(self):
        """Test .jsonl extension."""
        result = get_exporter_for_extension(".jsonl")
        assert result == ExporterType.JSONL
    
    def test_ndjson_extension(self):
        """Test .ndjson maps to JSONL."""
        result = get_exporter_for_extension(".ndjson")
        assert result == ExporterType.JSONL
    
    def test_md_extension(self):
        """Test .md extension."""
        result = get_exporter_for_extension(".md")
        assert result == ExporterType.MARKDOWN
    
    def test_markdown_extension(self):
        """Test .markdown extension."""
        result = get_exporter_for_extension(".markdown")
        assert result == ExporterType.MARKDOWN
    
    def test_csv_extension(self):
        """Test .csv extension."""
        result = get_exporter_for_extension(".csv")
        assert result == ExporterType.CSV
    
    def test_tsv_extension(self):
        """Test .tsv extension."""
        result = get_exporter_for_extension(".tsv")
        assert result == ExporterType.TSV
    
    def test_unknown_extension_defaults_to_json(self):
        """Test unknown extension defaults to JSON."""
        result = get_exporter_for_extension(".xyz")
        assert result == ExporterType.JSON
    
    def test_case_insensitive(self):
        """Test case insensitivity."""
        result = get_exporter_for_extension(".JSON")
        assert result == ExporterType.JSON


class TestExporterType:
    """Tests for ExporterType enum."""
    
    def test_all_types_exist(self):
        """Test all expected types exist."""
        assert ExporterType.JSON
        assert ExporterType.JSONL
        assert ExporterType.MARKDOWN
        assert ExporterType.MARKDOWN_SINGLE
        assert ExporterType.CSV
        assert ExporterType.TSV
        assert ExporterType.CSV_FLAT
    
    def test_type_values(self):
        """Test type values are correct strings."""
        assert ExporterType.JSON.value == "json"
        assert ExporterType.JSONL.value == "jsonl"
        assert ExporterType.MARKDOWN.value == "markdown"
        assert ExporterType.CSV.value == "csv"

