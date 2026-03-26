"""Markdown exporter implementation."""

import logging
from typing import List, Optional
from datetime import datetime

from .base import BaseExporter, ExportConfig, ScrapingResult, ScrapingStats

logger = logging.getLogger(__name__)


class MarkdownExporter(BaseExporter):
    """
    Export scraping results to Markdown format.
    
    Features:
    - Clean, readable output
    - Table of contents generation
    - Preserved headings and structure
    - Link formatting
    """
    
    @property
    def format_name(self) -> str:
        return "markdown"
    
    @property
    def file_extension(self) -> str:
        return ".md"
    
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """Export results to Markdown string."""
        sections = []
        
        # Title
        sections.append("# Web Scraping Results\n")
        
        # Metadata
        if self.config.include_metadata:
            sections.append(self._generate_metadata_section())
        
        # Statistics
        if self.config.include_stats and stats:
            sections.append(self._generate_stats_section(stats))
        
        # Table of contents
        if self.config.include_toc and len(results) > 1:
            sections.append(self._generate_toc(results))
        
        # Results
        sections.append("## Pages\n")
        for i, result in enumerate(results, 1):
            sections.append(self._format_result(result, i))
        
        return "\n".join(sections)
    
    def _generate_metadata_section(self) -> str:
        """Generate metadata section."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""## Export Information

- **Exported at:** {now}
- **Format:** Markdown

---
"""
    
    def _generate_stats_section(self, stats: ScrapingStats) -> str:
        """Generate statistics section."""
        return f"""## Scraping Statistics

| Metric | Value |
|--------|-------|
| Total Pages | {stats.total_pages} |
| Successful | {stats.successful_pages} |
| Failed | {stats.failed_pages} |
| Success Rate | {(stats.successful_pages / max(stats.total_pages, 1) * 100):.1f}% |
| Duration | {stats._format_duration()} |
| Start URL | {stats.start_url} |
| Domain | {stats.domain} |

---
"""
    
    def _generate_toc(self, results: List[ScrapingResult]) -> str:
        """Generate table of contents."""
        lines = ["## Table of Contents\n"]
        
        for i, result in enumerate(results, 1):
            title = result.title or f"Page {i}"
            # Create anchor-friendly ID
            anchor = self._create_anchor(title, i)
            lines.append(f"{i}. [{title}](#{anchor})")
        
        lines.append("\n---\n")
        return "\n".join(lines)
    
    def _create_anchor(self, title: str, index: int) -> str:
        """Create markdown anchor from title."""
        # Simplified anchor creation
        anchor = title.lower()
        anchor = "".join(c if c.isalnum() or c == '-' else '-' for c in anchor)
        anchor = "-".join(filter(None, anchor.split("-")))
        return f"page-{index}-{anchor[:30]}" if anchor else f"page-{index}"
    
    def _format_result(self, result: ScrapingResult, index: int) -> str:
        """Format a single result as Markdown."""
        title = result.title or f"Page {index}"
        anchor = self._create_anchor(title, index)
        
        level = self.config.heading_level
        heading = "#" * level
        
        sections = []
        
        # Page header
        sections.append(f'<a id="{anchor}"></a>')
        sections.append(f"{heading} {index}. {title}\n")
        
        # URL
        sections.append(f"**URL:** [{result.url}]({result.url})\n")
        
        # Metadata
        if result.meta_description:
            sections.append(f"**Description:** {result.meta_description}\n")
        
        if result.topics:
            sections.append(f"**Topics:** {', '.join(result.topics)}\n")
        
        if result.content_type != "unknown":
            sections.append(f"**Content Type:** {result.content_type}\n")
        
        # Summary
        if result.summary:
            sections.append(f"\n### Summary\n\n{result.summary}\n")
        
        # Main content
        if result.content:
            content = result.content
            if self.config.max_content_length:
                content = content[:self.config.max_content_length]
                if len(result.content) > self.config.max_content_length:
                    content += "\n\n*[Content truncated...]*"
            
            sections.append(f"\n### Content\n\n{content}\n")
        
        # Headings
        if result.headings:
            sections.append("\n### Page Headings\n")
            for level_name, headings in sorted(result.headings.items()):
                for heading_text in headings[:5]:  # Limit to 5 per level
                    sections.append(f"- **{level_name.upper()}:** {heading_text}")
            sections.append("")
        
        # Links
        if self.config.include_links and result.links:
            sections.append("\n### Links Found\n")
            for link in result.links[:10]:  # Limit to 10 links
                text = link.get("text", "")[:50] or "No text"
                url = link.get("url", "")
                sections.append(f"- [{text}]({url})")
            
            if len(result.links) > 10:
                sections.append(f"\n*... and {len(result.links) - 10} more links*")
            sections.append("")
        
        # Separator
        sections.append("\n---\n")
        
        return "\n".join(sections)


class SinglePageMarkdownExporter(MarkdownExporter):
    """
    Export a single page result optimized for readability.
    
    This is useful when scraping a single page and wanting
    clean, article-like output.
    """
    
    @property
    def format_name(self) -> str:
        return "markdown-single"
    
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """Export single result as clean Markdown."""
        if not results:
            return "# No Results\n\nNo pages were scraped."
        
        result = results[0]
        sections = []
        
        # Title
        title = result.title or "Untitled Page"
        sections.append(f"# {title}\n")
        
        # Source
        sections.append(f"> Source: [{result.url}]({result.url})\n")
        
        # Metadata line
        meta_parts = []
        if result.content_type != "unknown":
            meta_parts.append(f"Type: {result.content_type}")
        if result.topics:
            meta_parts.append(f"Topics: {', '.join(result.topics)}")
        if meta_parts:
            sections.append(f"*{' | '.join(meta_parts)}*\n")
        
        # Summary
        if result.summary:
            sections.append("## Summary\n")
            sections.append(f"{result.summary}\n")
        
        # Main content
        if result.content:
            sections.append("## Content\n")
            sections.append(result.content)
        
        return "\n".join(sections)
