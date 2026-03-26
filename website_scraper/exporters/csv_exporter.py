"""CSV exporter implementation."""

import csv
import io
import logging
from typing import List, Optional, Dict, Any

from .base import BaseExporter, ExportConfig, ScrapingResult, ScrapingStats

logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """
    Export scraping results to CSV format.
    
    Features:
    - Configurable columns
    - Flattening of nested data
    - Proper escaping and quoting
    """
    
    # Default columns to export
    DEFAULT_COLUMNS = [
        "url",
        "title",
        "meta_description",
        "content",
        "summary",
        "content_type",
        "topics",
        "status_code",
        "load_time_ms",
        "scraped_at",
    ]
    
    def __init__(
        self,
        config: Optional[ExportConfig] = None,
        columns: Optional[List[str]] = None,
    ):
        """
        Initialize CSV exporter.
        
        Args:
            config: Export configuration
            columns: List of columns to include (default: DEFAULT_COLUMNS)
        """
        super().__init__(config)
        self.columns = columns or self.DEFAULT_COLUMNS
    
    @property
    def format_name(self) -> str:
        return "csv"
    
    @property
    def file_extension(self) -> str:
        return ".csv"
    
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """Export results to CSV string."""
        output = io.StringIO()
        
        writer = csv.writer(
            output,
            delimiter=self.config.csv_delimiter,
            quoting=self.config.csv_quoting,
        )
        
        # Write header
        writer.writerow(self.columns)
        
        # Write data rows
        for result in results:
            row = self._result_to_row(result)
            writer.writerow(row)
        
        return output.getvalue()
    
    def _result_to_row(self, result: ScrapingResult) -> List[str]:
        """Convert a result to a CSV row."""
        data = result.to_dict()
        row = []
        
        for column in self.columns:
            value = data.get(column, "")
            
            # Handle special types
            if isinstance(value, list):
                # Join lists with semicolons
                if value and isinstance(value[0], dict):
                    # Handle list of dicts (e.g., links)
                    value = "; ".join(str(item.get("url", item)) for item in value[:5])
                else:
                    value = "; ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Flatten dict to key-value pairs
                value = "; ".join(f"{k}: {v}" for k, v in value.items())
            elif value is None:
                value = ""
            else:
                value = str(value)
            
            # Truncate long content
            if column == "content" and self.config.max_content_length:
                value = value[:self.config.max_content_length]
            
            row.append(value)
        
        return row
    
    async def export_with_stats(
        self,
        results: List[ScrapingResult],
        stats: ScrapingStats,
    ) -> str:
        """
        Export results with statistics as a separate section.
        
        Returns CSV with a blank line separator between stats and data.
        """
        sections = []
        
        # Stats section
        if self.config.include_stats:
            stats_output = io.StringIO()
            stats_writer = csv.writer(stats_output, delimiter=self.config.csv_delimiter)
            
            stats_writer.writerow(["# Statistics"])
            stats_dict = stats.to_dict()
            for key, value in stats_dict.items():
                stats_writer.writerow([f"# {key}", str(value)])
            stats_writer.writerow([])  # Blank line
            
            sections.append(stats_output.getvalue())
        
        # Data section
        data_content = await self.export(results, stats)
        sections.append(data_content)
        
        return "".join(sections)


class TSVExporter(CSVExporter):
    """
    Export scraping results to TSV (Tab-Separated Values) format.
    """
    
    def __init__(
        self,
        config: Optional[ExportConfig] = None,
        columns: Optional[List[str]] = None,
    ):
        """Initialize TSV exporter."""
        super().__init__(config, columns)
        if self.config:
            self.config.csv_delimiter = "\t"
        else:
            self.config = ExportConfig(csv_delimiter="\t")
    
    @property
    def format_name(self) -> str:
        return "tsv"
    
    @property
    def file_extension(self) -> str:
        return ".tsv"


class FlatCSVExporter(CSVExporter):
    """
    Export fully flattened CSV with all available fields.
    
    This exporter automatically discovers all fields in the results
    and creates columns for each unique field found.
    """
    
    @property
    def format_name(self) -> str:
        return "csv-flat"
    
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """Export results with auto-discovered columns."""
        if not results:
            return ""
        
        # Discover all columns
        all_columns = set()
        flattened_results = []
        
        for result in results:
            flat = self._flatten_dict(result.to_dict())
            flattened_results.append(flat)
            all_columns.update(flat.keys())
        
        # Sort columns for consistent output
        columns = sorted(all_columns)
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(
            output,
            delimiter=self.config.csv_delimiter,
            quoting=self.config.csv_quoting,
        )
        
        # Header
        writer.writerow(columns)
        
        # Data
        for flat in flattened_results:
            row = [str(flat.get(col, "")) for col in columns]
            writer.writerow(row)
        
        return output.getvalue()
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = "",
        sep: str = "_",
    ) -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    # For list of dicts, just count
                    items.append((f"{new_key}_count", len(v)))
                else:
                    # Join simple lists
                    items.append((new_key, "; ".join(str(x) for x in v)))
            else:
                items.append((new_key, v))
        
        return dict(items)
