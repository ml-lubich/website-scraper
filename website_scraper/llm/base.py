"""Base classes and interfaces for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class ContentType(Enum):
    """Types of content that can be extracted."""
    MAIN_CONTENT = "main_content"
    NAVIGATION = "navigation"
    ADVERTISEMENT = "advertisement"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    HEADER = "header"
    FORM = "form"
    COMMENT = "comment"
    METADATA = "metadata"
    UNKNOWN = "unknown"


@dataclass
class ExtractedContent:
    """Structured content extracted from a page by LLM."""
    
    # Main content
    title: str = ""
    main_content: str = ""
    summary: str = ""
    
    # Structured data
    headings: List[str] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    lists: List[List[str]] = field(default_factory=list)
    
    # Metadata
    author: Optional[str] = None
    date_published: Optional[str] = None
    date_modified: Optional[str] = None
    language: Optional[str] = None
    
    # Classification
    content_type: str = "article"
    topics: List[str] = field(default_factory=list)
    
    # Quality indicators
    confidence_score: float = 0.0
    extraction_notes: str = ""
    
    # Raw data for debugging
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "main_content": self.main_content,
            "summary": self.summary,
            "headings": self.headings,
            "paragraphs": self.paragraphs,
            "lists": self.lists,
            "author": self.author,
            "date_published": self.date_published,
            "date_modified": self.date_modified,
            "language": self.language,
            "content_type": self.content_type,
            "topics": self.topics,
            "confidence_score": self.confidence_score,
            "extraction_notes": self.extraction_notes,
        }


@dataclass
class ScoredLink:
    """A link with relevance scoring from LLM analysis."""
    
    url: str
    text: str
    
    # Relevance scores (0-1)
    relevance_score: float = 0.0
    priority: int = 0  # 1 = highest, 5 = lowest
    
    # Classification
    link_type: str = "content"  # content, navigation, external, download, etc.
    expected_content_type: str = "unknown"
    
    # Reasoning
    reasoning: str = ""
    should_follow: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "text": self.text,
            "relevance_score": self.relevance_score,
            "priority": self.priority,
            "link_type": self.link_type,
            "expected_content_type": self.expected_content_type,
            "reasoning": self.reasoning,
            "should_follow": self.should_follow,
        }


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    
    # API settings
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    
    # Model settings
    model: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    
    # Request settings
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Content settings
    max_content_length: int = 100000  # Characters to send to LLM
    include_html: bool = False  # Send raw HTML vs extracted text
    
    # Feature flags
    enable_content_extraction: bool = True
    enable_link_analysis: bool = True
    enable_summarization: bool = True


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers (OpenAI, Anthropic, Gemini, Ollama) must implement
    this interface to be used with the scraper.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the LLM provider.
        
        Args:
            config: Configuration for the provider
        """
        self.config = config or LLMConfig()
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass
    
    @abstractmethod
    async def analyze_content(
        self,
        html: str,
        url: str,
        extraction_goal: Optional[str] = None,
    ) -> ExtractedContent:
        """
        Analyze page content and extract structured data.
        
        This method uses the LLM to intelligently extract the main content
        from a page, filtering out navigation, ads, and other non-essential
        elements.
        
        Args:
            html: Raw HTML or text content of the page
            url: URL of the page (for context)
            extraction_goal: Optional specific extraction instructions
            
        Returns:
            ExtractedContent with structured page data
        """
        pass
    
    @abstractmethod
    async def analyze_links(
        self,
        links: List[Dict[str, str]],
        page_context: str,
        crawl_goal: Optional[str] = None,
    ) -> List[ScoredLink]:
        """
        Analyze and score links for relevance.
        
        This method uses the LLM to determine which links are worth
        following based on the crawl goal and page context.
        
        Args:
            links: List of link dictionaries with 'url' and 'text' keys
            page_context: Context about the current page (title, summary)
            crawl_goal: Optional description of what we're looking for
            
        Returns:
            List of ScoredLink objects sorted by relevance
        """
        pass
    
    @abstractmethod
    async def summarize_content(
        self,
        content: str,
        max_length: int = 500,
    ) -> str:
        """
        Generate a summary of the content.
        
        Args:
            content: Text content to summarize
            max_length: Maximum length of summary in characters
            
        Returns:
            Summary text
        """
        pass
    
    async def is_available(self) -> bool:
        """
        Check if the provider is available and configured correctly.
        
        Returns:
            True if provider is ready to use
        """
        return self.config.api_key is not None or self.provider_name == "ollama"
    
    def _truncate_content(self, content: str) -> str:
        """
        Truncate content to fit within LLM context limits.
        
        Args:
            content: Content to truncate
            
        Returns:
            Truncated content
        """
        if len(content) <= self.config.max_content_length:
            return content
        
        # Truncate with ellipsis
        return content[:self.config.max_content_length - 100] + "\n\n[Content truncated...]"
    
    def _get_content_extraction_prompt(
        self,
        url: str,
        extraction_goal: Optional[str] = None,
    ) -> str:
        """
        Generate the prompt for content extraction.
        
        Args:
            url: URL of the page
            extraction_goal: Optional specific extraction instructions
            
        Returns:
            Prompt string
        """
        goal_text = f"\nSpecific goal: {extraction_goal}" if extraction_goal else ""
        
        return f"""Analyze the following web page content and extract structured information.

URL: {url}{goal_text}

Your task:
1. Identify and extract the MAIN CONTENT of the page (article, product description, etc.)
2. Filter out navigation menus, advertisements, sidebars, and boilerplate content
3. Extract metadata like title, author, date if available
4. Identify the content type (article, product, listing, etc.)
5. List the main topics covered

Respond in JSON format with the following structure:
{{
    "title": "Page title",
    "main_content": "The main text content, cleaned and formatted",
    "summary": "A 2-3 sentence summary",
    "headings": ["List", "of", "headings"],
    "author": "Author name if found",
    "date_published": "Publication date if found",
    "language": "Content language (e.g., 'en')",
    "content_type": "article/product/listing/documentation/other",
    "topics": ["topic1", "topic2"],
    "confidence_score": 0.0-1.0
}}

PAGE CONTENT:
"""
    
    def _get_link_analysis_prompt(
        self,
        page_context: str,
        crawl_goal: Optional[str] = None,
    ) -> str:
        """
        Generate the prompt for link analysis.
        
        Args:
            page_context: Context about the current page
            crawl_goal: Optional description of what we're looking for
            
        Returns:
            Prompt string
        """
        goal_text = f"\nCrawl goal: {crawl_goal}" if crawl_goal else ""
        
        return f"""Analyze the following links from a web page and score them by relevance for crawling.

Current page context: {page_context}{goal_text}

For each link, determine:
1. Relevance score (0.0-1.0) - how relevant is this link to the crawl goal?
2. Priority (1-5) - 1 is highest priority, 5 is lowest
3. Link type - content, navigation, external, download, social, etc.
4. Should we follow this link? (true/false)
5. Brief reasoning for your decision

Respond in JSON format with an array of analyzed links:
{{
    "links": [
        {{
            "url": "link url",
            "relevance_score": 0.0-1.0,
            "priority": 1-5,
            "link_type": "content/navigation/external/etc",
            "should_follow": true/false,
            "reasoning": "Brief explanation"
        }}
    ]
}}

Focus on identifying high-value content links and filtering out:
- Navigation/menu links
- Social media share buttons
- Login/signup links
- Footer links
- Advertisement links

LINKS TO ANALYZE:
"""

