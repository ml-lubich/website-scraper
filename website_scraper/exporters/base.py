"""Base exporter class and configuration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExportConfig:
    """Configuration for exporters."""
    
    # Output settings
    output_path: Optional[str] = None
    pretty_print: bool = True
    include_metadata: bool = True
    include_stats: bool = True
    
    # Content settings
    include_raw_html: bool = False
    include_links: bool = True
    include_images: bool = False
    max_content_length: Optional[int] = None
    
    # CSV specific
    csv_delimiter: str = ","
    csv_quoting: int = 1  # csv.QUOTE_MINIMAL
    flatten_nested: bool = True
    
    # Markdown specific
    include_toc: bool = True
    heading_level: int = 2
    
    # Streaming settings
    streaming: bool = False
    chunk_size: int = 100


@dataclass
class ScrapingResult:
    """Result from scraping a single page."""
    
    url: str
    title: str = ""
    content: str = ""
    meta_description: Optional[str] = None
    headings: Dict[str, List[str]] = field(default_factory=dict)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    
    # LLM enhanced fields
    summary: str = ""
    topics: List[str] = field(default_factory=list)
    content_type: str = "unknown"
    
    # Metadata
    scraped_at: str = ""
    load_time_ms: float = 0.0
    status_code: int = 200
    
    # Raw data
    raw_html: Optional[str] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "meta_description": self.meta_description,
            "headings": self.headings,
            "links": self.links,
            "images": self.images,
            "summary": self.summary,
            "topics": self.topics,
            "content_type": self.content_type,
            "scraped_at": self.scraped_at,
            "load_time_ms": self.load_time_ms,
            "status_code": self.status_code,
        }
        
        if self.raw_html:
            data["raw_html"] = self.raw_html
        
        if self.llm_analysis:
            data["llm_analysis"] = self.llm_analysis
        
        return data


@dataclass
class ScrapingStats:
    """Statistics from a scraping session."""
    
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    total_links_found: int = 0
    total_links_followed: int = 0
    
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    
    start_url: str = ""
    domain: str = ""
    
    # Performance metrics
    avg_load_time_ms: float = 0.0
    total_bytes_downloaded: int = 0
    
    # LLM usage
    llm_provider: Optional[str] = None
    llm_calls: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_pages": self.total_pages,
            "successful_pages": self.successful_pages,
            "failed_pages": self.failed_pages,
            "success_rate": f"{(self.successful_pages / max(self.total_pages, 1) * 100):.1f}%",
            "total_links_found": self.total_links_found,
            "total_links_followed": self.total_links_followed,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self._format_duration(),
            "start_url": self.start_url,
            "domain": self.domain,
            "avg_load_time_ms": self.avg_load_time_ms,
            "total_bytes_downloaded": self.total_bytes_downloaded,
            "llm_provider": self.llm_provider,
            "llm_calls": self.llm_calls,
        }
    
    def _format_duration(self) -> str:
        """Format duration as human-readable string."""
        seconds = self.duration_seconds
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"


class BaseExporter(ABC):
    """
    Abstract base class for exporters.
    
    All exporters must implement the export method to write
    scraping results to their target format.
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize exporter.
        
        Args:
            config: Export configuration
        """
        self.config = config or ExportConfig()
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the name of this export format."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        pass
    
    @abstractmethod
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """
        Export scraping results.
        
        Args:
            results: List of scraping results
            stats: Optional scraping statistics
            
        Returns:
            Exported content as string
        """
        pass
    
    async def export_to_file(
        self,
        results: List[ScrapingResult],
        output_path: str,
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """
        Export results to a file.
        
        Args:
            results: List of scraping results
            output_path: Path to output file
            stats: Optional scraping statistics
            
        Returns:
            Path to the created file
        """
        content = await self.export(results, stats)
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add extension if not present
        if not path.suffix:
            path = path.with_suffix(self.file_extension)
        
        path.write_text(content, encoding='utf-8')
        logger.info(f"Exported {len(results)} results to {path}")
        
        return str(path)
    
    def _filter_result(self, result: ScrapingResult) -> Dict[str, Any]:
        """Filter result based on config settings."""
        data = result.to_dict()
        
        if not self.config.include_raw_html:
            data.pop("raw_html", None)
        
        if not self.config.include_links:
            data.pop("links", None)
        
        if not self.config.include_images:
            data.pop("images", None)
        
        if self.config.max_content_length and "content" in data:
            data["content"] = data["content"][:self.config.max_content_length]
        
        return data
