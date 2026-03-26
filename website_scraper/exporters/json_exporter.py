"""JSON exporter implementation."""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import BaseExporter, ExportConfig, ScrapingResult, ScrapingStats

logger = logging.getLogger(__name__)


class JSONExporter(BaseExporter):
    """
    Export scraping results to JSON format.
    
    Features:
    - Pretty-printed or compact output
    - Optional metadata and statistics
    - Streaming support for large datasets
    """
    
    @property
    def format_name(self) -> str:
        return "json"
    
    @property
    def file_extension(self) -> str:
        return ".json"
    
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """Export results to JSON string."""
        output: Dict[str, Any] = {}
        
        # Add metadata
        if self.config.include_metadata:
            output["metadata"] = {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "format": "json",
                "version": "1.0",
                "total_results": len(results),
            }
        
        # Add statistics
        if self.config.include_stats and stats:
            output["stats"] = stats.to_dict()
        
        # Add results
        output["data"] = [
            self._filter_result(result)
            for result in results
        ]
        
        # Format output
        if self.config.pretty_print:
            return json.dumps(output, indent=2, ensure_ascii=False, default=str)
        else:
            return json.dumps(output, ensure_ascii=False, default=str)
    
    async def export_streaming(
        self,
        results: List[ScrapingResult],
        output_path: str,
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """
        Export results using streaming for large datasets.
        
        This writes results incrementally to avoid memory issues
        with very large result sets.
        """
        import aiofiles
        
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            # Write opening
            await f.write('{\n')
            
            # Write metadata
            if self.config.include_metadata:
                metadata = {
                    "exported_at": datetime.utcnow().isoformat() + "Z",
                    "format": "json",
                    "version": "1.0",
                    "total_results": len(results),
                }
                await f.write(f'  "metadata": {json.dumps(metadata)},\n')
            
            # Write stats
            if self.config.include_stats and stats:
                await f.write(f'  "stats": {json.dumps(stats.to_dict())},\n')
            
            # Write data array
            await f.write('  "data": [\n')
            
            for i, result in enumerate(results):
                data = self._filter_result(result)
                line = json.dumps(data, ensure_ascii=False, default=str)
                
                if i < len(results) - 1:
                    await f.write(f'    {line},\n')
                else:
                    await f.write(f'    {line}\n')
            
            # Close data array and object
            await f.write('  ]\n')
            await f.write('}\n')
        
        logger.info(f"Streamed {len(results)} results to {output_path}")
        return output_path


class JSONLExporter(BaseExporter):
    """
    Export scraping results to JSON Lines format.
    
    Each result is a separate JSON object on its own line,
    making it easier to process large files line by line.
    """
    
    @property
    def format_name(self) -> str:
        return "jsonl"
    
    @property
    def file_extension(self) -> str:
        return ".jsonl"
    
    async def export(
        self,
        results: List[ScrapingResult],
        stats: Optional[ScrapingStats] = None,
    ) -> str:
        """Export results to JSON Lines string."""
        lines = []
        
        # Add metadata line
        if self.config.include_metadata:
            metadata = {
                "_type": "metadata",
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "format": "jsonl",
                "total_results": len(results),
            }
            lines.append(json.dumps(metadata, ensure_ascii=False))
        
        # Add stats line
        if self.config.include_stats and stats:
            stats_data = stats.to_dict()
            stats_data["_type"] = "stats"
            lines.append(json.dumps(stats_data, ensure_ascii=False))
        
        # Add result lines
        for result in results:
            data = self._filter_result(result)
            data["_type"] = "result"
            lines.append(json.dumps(data, ensure_ascii=False, default=str))
        
        return "\n".join(lines)
