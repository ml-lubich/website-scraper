"""Factory for creating exporters."""

import logging
from enum import Enum
from typing import Optional

from .base import BaseExporter, ExportConfig
from .json_exporter import JSONExporter, JSONLExporter
from .markdown_exporter import MarkdownExporter, SinglePageMarkdownExporter
from .csv_exporter import CSVExporter, TSVExporter, FlatCSVExporter

logger = logging.getLogger(__name__)


class ExporterType(Enum):
    """Available exporter types."""
    JSON = "json"
    JSONL = "jsonl"
    MARKDOWN = "markdown"
    MARKDOWN_SINGLE = "markdown-single"
    CSV = "csv"
    TSV = "tsv"
    CSV_FLAT = "csv-flat"


def create_exporter(
    exporter_type: ExporterType | str,
    config: Optional[ExportConfig] = None,
) -> BaseExporter:
    """
    Create an exporter instance.
    
    Args:
        exporter_type: Type of exporter to create
        config: Optional export configuration
        
    Returns:
        Configured exporter instance
        
    Raises:
        ValueError: If exporter type is unknown
    """
    # Handle string input
    if isinstance(exporter_type, str):
        exporter_type = exporter_type.lower()
        try:
            exporter_type = ExporterType(exporter_type)
        except ValueError:
            raise ValueError(
                f"Unknown exporter type: {exporter_type}. "
                f"Available: {[e.value for e in ExporterType]}"
            )
    
    config = config or ExportConfig()
    
    if exporter_type == ExporterType.JSON:
        logger.debug("Creating JSON exporter")
        return JSONExporter(config)
    
    elif exporter_type == ExporterType.JSONL:
        logger.debug("Creating JSON Lines exporter")
        return JSONLExporter(config)
    
    elif exporter_type == ExporterType.MARKDOWN:
        logger.debug("Creating Markdown exporter")
        return MarkdownExporter(config)
    
    elif exporter_type == ExporterType.MARKDOWN_SINGLE:
        logger.debug("Creating single-page Markdown exporter")
        return SinglePageMarkdownExporter(config)
    
    elif exporter_type == ExporterType.CSV:
        logger.debug("Creating CSV exporter")
        return CSVExporter(config)
    
    elif exporter_type == ExporterType.TSV:
        logger.debug("Creating TSV exporter")
        return TSVExporter(config)
    
    elif exporter_type == ExporterType.CSV_FLAT:
        logger.debug("Creating flat CSV exporter")
        return FlatCSVExporter(config)
    
    else:
        raise ValueError(f"Unknown exporter type: {exporter_type}")


def get_exporter_for_extension(extension: str) -> ExporterType:
    """
    Get the appropriate exporter type for a file extension.
    
    Args:
        extension: File extension (with or without leading dot)
        
    Returns:
        Appropriate ExporterType
    """
    ext = extension.lower().lstrip(".")
    
    mapping = {
        "json": ExporterType.JSON,
        "jsonl": ExporterType.JSONL,
        "ndjson": ExporterType.JSONL,
        "md": ExporterType.MARKDOWN,
        "markdown": ExporterType.MARKDOWN,
        "csv": ExporterType.CSV,
        "tsv": ExporterType.TSV,
    }
    
    return mapping.get(ext, ExporterType.JSON)
