"""Google Gemini provider for LLM-powered content extraction."""

import json
import logging
from typing import List, Dict, Optional

from .base import (
    BaseLLMProvider,
    LLMConfig,
    ExtractedContent,
    ScoredLink,
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider for intelligent content extraction.
    
    Uses Google's Gemini API to analyze web pages and extract structured content.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize Gemini provider."""
        super().__init__(config)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self.genai = genai
            self.model_name = self.config.model or "gemini-pro"
        except ImportError:
            raise ImportError(
                "Gemini provider requires 'google-generativeai' package. "
                "Install with: pip install website-scraper[gemini]"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "gemini"
    
    @property
    def default_model(self) -> str:
        """Return default model."""
        return self.model_name
    
    async def analyze_content(
        self,
        html: str,
        url: str,
        extraction_goal: Optional[str] = None,
    ) -> ExtractedContent:
        """
        Analyze page content and extract structured data.
        
        Args:
            html: Raw HTML or text content
            url: URL of the page
            extraction_goal: Optional extraction instructions
            
        Returns:
            ExtractedContent with structured data
        """
        import asyncio
        
        # Truncate content
        content = self._truncate_content(html)
        
        # Generate prompt
        prompt = self._get_content_extraction_prompt(url, extraction_goal)
        full_prompt = prompt + content
        
        try:
            model = self.genai.GenerativeModel(self.default_model)
            
            # Gemini API is sync, so run in executor
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                },
            )
            
            content_text = response.text if hasattr(response, "text") else str(response)
            if not content_text:
                raise ValueError("Empty response from Gemini")
            
            # Parse JSON
            try:
                data = json.loads(content_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                else:
                    json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(0))
                    else:
                        raise ValueError("No JSON found in response")
            
            # Convert to ExtractedContent
            return ExtractedContent(
                title=data.get("title", ""),
                main_content=data.get("main_content", ""),
                summary=data.get("summary", ""),
                headings=data.get("headings", []),
                paragraphs=data.get("paragraphs", []),
                author=data.get("author"),
                date_published=data.get("date_published"),
                date_modified=data.get("date_modified"),
                language=data.get("language"),
                content_type=data.get("content_type", "unknown"),
                topics=data.get("topics", []),
                confidence_score=float(data.get("confidence_score", 0.0)),
                extraction_notes=data.get("extraction_notes", ""),
                raw_response={"response": content_text},
            )
            
        except Exception as e:
            logger.error(f"Gemini content analysis failed: {e}")
            return ExtractedContent(
                title="",
                main_content="",
                summary=f"Error: {str(e)}",
                confidence_score=0.0,
            )
    
    async def analyze_links(
        self,
        links: List[Dict[str, str]],
        page_context: str,
        crawl_goal: Optional[str] = None,
    ) -> List[ScoredLink]:
        """
        Analyze and score links for relevance.
        
        Args:
            links: List of link dictionaries
            page_context: Context about current page
            crawl_goal: Optional crawl goal description
            
        Returns:
            List of ScoredLink objects
        """
        import asyncio
        
        if not links:
            return []
        
        # Format links for prompt
        links_text = "\n".join([
            f"- {link.get('url', '')}: {link.get('text', '')[:100]}"
            for link in links[:50]
        ])
        
        # Generate prompt
        prompt = self._get_link_analysis_prompt(page_context, crawl_goal)
        full_prompt = prompt + links_text
        
        try:
            model = self.genai.GenerativeModel(self.default_model)
            
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                },
            )
            
            content_text = response.text if hasattr(response, "text") else str(response)
            if not content_text:
                return []
            
            # Parse JSON
            try:
                data = json.loads(content_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    return []
            
            # Convert to ScoredLink objects
            scored_links = []
            links_data = data.get("links", [])
            
            for link_data in links_data:
                scored_link = ScoredLink(
                    url=link_data.get("url", ""),
                    text=link_data.get("text", ""),
                    relevance_score=float(link_data.get("relevance_score", 0.0)),
                    priority=int(link_data.get("priority", 5)),
                    link_type=link_data.get("link_type", "unknown"),
                    expected_content_type=link_data.get("expected_content_type", "unknown"),
                    reasoning=link_data.get("reasoning", ""),
                    should_follow=bool(link_data.get("should_follow", True)),
                )
                scored_links.append(scored_link)
            
            # Sort by relevance score
            scored_links.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return scored_links
            
        except Exception as e:
            logger.error(f"Gemini link analysis failed: {e}")
            return [
                ScoredLink(
                    url=link.get("url", ""),
                    text=link.get("text", ""),
                    relevance_score=0.5,
                    should_follow=True,
                )
                for link in links
            ]
    
    async def summarize_content(
        self,
        content: str,
        max_length: int = 500,
    ) -> str:
        """
        Generate a summary of the content.
        
        Args:
            content: Text content to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summary text
        """
        import asyncio
        
        content = self._truncate_content(content)
        
        prompt = f"""Summarize the following content in {max_length} characters or less:

{content}

Summary:"""
        
        try:
            model = self.genai.GenerativeModel(self.default_model)
            
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": min(max_length // 4, 500),
                },
            )
            
            summary = response.text if hasattr(response, "text") else str(response)
            return summary[:max_length]
            
        except Exception as e:
            logger.error(f"Gemini summarization failed: {e}")
            return content[:max_length] + "..." if len(content) > max_length else content
