"""Ollama (local LLM) provider implementation."""

import json
import logging
from typing import Optional, List, Dict, Any

import aiohttp

from .base import BaseLLMProvider, LLMConfig, ExtractedContent, ScoredLink

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider for local models.
    
    Ollama must be running locally. No additional packages required.
    Default endpoint: http://localhost:11434
    
    Common models: llama2, mistral, codellama, neural-chat
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize Ollama provider."""
        super().__init__(config)
        if not self.config.api_base_url:
            self.config.api_base_url = "http://localhost:11434"
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "ollama"
    
    @property
    def default_model(self) -> str:
        """Return default model."""
        return "llama3.2"
    
    async def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.api_base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = True,
    ) -> str:
        """Generate response from Ollama."""
        url = f"{self.config.api_base_url}/api/generate"
        
        payload = {
            "model": self.config.model or self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        
        if system:
            payload["system"] = system
        
        if json_mode:
            payload["format"] = "json"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result.get("response", "")
    
    async def analyze_content(
        self,
        html: str,
        url: str,
        extraction_goal: Optional[str] = None,
    ) -> ExtractedContent:
        """Extract structured content using Ollama."""
        content = self._truncate_content(html)
        prompt = self._get_content_extraction_prompt(url, extraction_goal)
        
        system = (
            "You are an expert web content extractor. Extract structured data from "
            "web pages accurately. Always respond with valid JSON matching the requested format."
        )
        
        try:
            response_text = await self._generate(
                f"{prompt}\n\n{content}",
                system=system,
                json_mode=True,
            )
            
            result = json.loads(response_text)
            
            return ExtractedContent(
                title=result.get("title", ""),
                main_content=result.get("main_content", ""),
                summary=result.get("summary", ""),
                headings=result.get("headings", []),
                paragraphs=result.get("paragraphs", []),
                author=result.get("author"),
                date_published=result.get("date_published"),
                language=result.get("language"),
                content_type=result.get("content_type", "unknown"),
                topics=result.get("topics", []),
                confidence_score=float(result.get("confidence_score", 0.0)),
                raw_response=result,
            )
            
        except Exception as e:
            logger.error(f"Ollama content extraction failed: {str(e)}")
            return ExtractedContent(
                extraction_notes=f"Extraction failed: {str(e)}",
                confidence_score=0.0,
            )
    
    async def analyze_links(
        self,
        links: List[Dict[str, str]],
        page_context: str,
        crawl_goal: Optional[str] = None,
    ) -> List[ScoredLink]:
        """Analyze and score links using Ollama."""
        if not links:
            return []
        
        links_to_analyze = links[:30]  # Ollama has smaller context, limit more
        links_text = "\n".join([
            f"- URL: {link.get('url', '')} | Text: {link.get('text', '')[:80]}"
            for link in links_to_analyze
        ])
        
        prompt = self._get_link_analysis_prompt(page_context, crawl_goal)
        
        system = (
            "You are an expert web crawler. Analyze links and determine which ones "
            "are worth following based on relevance. Always respond with valid JSON."
        )
        
        try:
            response_text = await self._generate(
                f"{prompt}\n\n{links_text}",
                system=system,
                json_mode=True,
            )
            
            result = json.loads(response_text)
            analyzed_links = result.get("links", [])
            
            scored_links = []
            for link_data in analyzed_links:
                scored_links.append(ScoredLink(
                    url=link_data.get("url", ""),
                    text=link_data.get("text", ""),
                    relevance_score=float(link_data.get("relevance_score", 0.0)),
                    priority=int(link_data.get("priority", 5)),
                    link_type=link_data.get("link_type", "unknown"),
                    reasoning=link_data.get("reasoning", ""),
                    should_follow=link_data.get("should_follow", False),
                ))
            
            scored_links.sort(key=lambda x: (-x.relevance_score, x.priority))
            return scored_links
            
        except Exception as e:
            logger.error(f"Ollama link analysis failed: {str(e)}")
            return [
                ScoredLink(
                    url=link.get("url", ""),
                    text=link.get("text", ""),
                    relevance_score=0.5,
                    should_follow=True,
                )
                for link in links_to_analyze
            ]
    
    async def summarize_content(
        self,
        content: str,
        max_length: int = 500,
    ) -> str:
        """Generate a summary using Ollama."""
        content = self._truncate_content(content)
        
        prompt = f"Summarize the following content in {max_length} characters or less. Be concise:\n\n{content}"
        system = "You are a professional summarizer. Create concise summaries that capture key points."
        
        try:
            response_text = await self._generate(
                prompt,
                system=system,
                json_mode=False,
            )
            
            return response_text.strip()[:max_length]
            
        except Exception as e:
            logger.error(f"Ollama summarization failed: {str(e)}")
            return ""
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.api_base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return [model["name"] for model in result.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
        
        return []

