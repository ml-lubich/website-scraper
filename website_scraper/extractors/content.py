"""Content extraction utilities for web pages."""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from html import unescape

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPageData:
    """Structured data extracted from a web page."""
    
    # Basic info
    url: str = ""
    title: str = ""
    
    # Content
    main_content: str = ""
    text: str = ""
    html: str = ""
    
    # Meta information
    meta_description: str = ""
    meta_keywords: List[str] = field(default_factory=list)
    language: str = ""
    
    # Structure
    headings: List[Dict[str, str]] = field(default_factory=list)  # [{level: h1, text: ...}]
    paragraphs: List[str] = field(default_factory=list)
    lists: List[List[str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)  # [{src, alt, title}]
    
    # Links
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    
    # Author/Date
    author: Optional[str] = None
    date_published: Optional[str] = None
    date_modified: Optional[str] = None
    
    # Status
    extraction_success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "title": self.title,
            "main_content": self.main_content,
            "text": self.text,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "language": self.language,
            "headings": self.headings,
            "author": self.author,
            "date_published": self.date_published,
            "date_modified": self.date_modified,
            "internal_links_count": len(self.internal_links),
            "external_links_count": len(self.external_links),
            "images_count": len(self.images),
            "extraction_success": self.extraction_success,
            "error": self.error,
        }


class ContentExtractor:
    """
    Extracts structured content from HTML pages.
    
    Uses BeautifulSoup for parsing and provides various methods
    for extracting different types of content.
    """
    
    # Tags to remove (noise)
    NOISE_TAGS = [
        "script", "style", "noscript", "iframe", "svg",
        "nav", "footer", "header", "aside", "form",
        "button", "input", "select", "textarea",
    ]
    
    # Tags that typically contain main content
    CONTENT_TAGS = ["article", "main", "div", "section"]
    
    # Content indicators in class/id names
    CONTENT_INDICATORS = [
        "content", "article", "post", "entry", "text",
        "body", "main", "story", "news",
    ]
    
    NOISE_INDICATORS = [
        "sidebar", "widget", "nav", "menu", "footer",
        "header", "comment", "ad", "advertisement",
        "social", "share", "related", "popular",
    ]
    
    def __init__(
        self,
        remove_noise: bool = True,
        extract_images: bool = True,
        max_content_length: int = 100000,
    ):
        """
        Initialize the content extractor.
        
        Args:
            remove_noise: Whether to remove noisy elements
            extract_images: Whether to extract image information
            max_content_length: Maximum content length to extract
        """
        self.remove_noise = remove_noise
        self.extract_images = extract_images
        self.max_content_length = max_content_length
    
    def extract(self, html: str, url: str = "") -> ExtractedPageData:
        """
        Extract structured content from HTML.
        
        Args:
            html: HTML content string
            url: URL of the page (for context)
            
        Returns:
            ExtractedPageData with extracted content
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup not installed. Run: pip install beautifulsoup4")
            return ExtractedPageData(
                url=url,
                extraction_success=False,
                error="BeautifulSoup not installed"
            )
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            data = ExtractedPageData(url=url, html=html)
            
            # Extract title
            data.title = self._extract_title(soup)
            
            # Extract meta information
            data.meta_description = self._extract_meta_description(soup)
            data.meta_keywords = self._extract_meta_keywords(soup)
            data.language = self._extract_language(soup)
            
            # Extract author and dates
            data.author = self._extract_author(soup)
            data.date_published = self._extract_date(soup, "published")
            data.date_modified = self._extract_date(soup, "modified")
            
            # Remove noise if configured
            if self.remove_noise:
                soup = self._remove_noise(soup)
            
            # Extract main content
            data.main_content = self._extract_main_content(soup)
            data.text = self._extract_text(soup)
            
            # Extract structure
            data.headings = self._extract_headings(soup)
            data.paragraphs = self._extract_paragraphs(soup)
            data.lists = self._extract_lists(soup)
            
            # Extract images
            if self.extract_images:
                data.images = self._extract_images(soup)
            
            # Extract links
            data.internal_links, data.external_links = self._extract_links(soup, url)
            
            data.extraction_success = True
            return data
            
        except Exception as e:
            logger.error(f"Content extraction failed: {str(e)}")
            return ExtractedPageData(
                url=url,
                html=html,
                extraction_success=False,
                error=str(e)
            )
    
    def _extract_title(self, soup: "BeautifulSoup") -> str:
        """Extract page title."""
        # Try title tag first
        if soup.title and soup.title.string:
            return str(soup.title.string).strip()
        
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        
        # Try first h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_meta_description(self, soup: "BeautifulSoup") -> str:
        """Extract meta description."""
        # Standard meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"].strip()
        
        # Open Graph description
        og = soup.find("meta", property="og:description")
        if og and og.get("content"):
            return og["content"].strip()
        
        return ""
    
    def _extract_meta_keywords(self, soup: "BeautifulSoup") -> List[str]:
        """Extract meta keywords."""
        meta = soup.find("meta", attrs={"name": "keywords"})
        if meta and meta.get("content"):
            keywords = meta["content"].split(",")
            return [k.strip() for k in keywords if k.strip()]
        return []
    
    def _extract_language(self, soup: "BeautifulSoup") -> str:
        """Extract page language."""
        # Check html tag
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            return html_tag["lang"]
        
        # Check meta tag
        meta = soup.find("meta", attrs={"http-equiv": "content-language"})
        if meta and meta.get("content"):
            return meta["content"]
        
        return ""
    
    def _extract_author(self, soup: "BeautifulSoup") -> Optional[str]:
        """Extract author information."""
        # Meta author
        meta = soup.find("meta", attrs={"name": "author"})
        if meta and meta.get("content"):
            return meta["content"].strip()
        
        # Schema.org author
        author_elem = soup.find(attrs={"itemprop": "author"})
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # rel="author"
        author_link = soup.find("a", attrs={"rel": "author"})
        if author_link:
            return author_link.get_text(strip=True)
        
        return None
    
    def _extract_date(self, soup: "BeautifulSoup", date_type: str = "published") -> Optional[str]:
        """Extract publication or modification date."""
        if date_type == "published":
            # Try various date properties
            for prop in ["article:published_time", "datePublished", "pubdate"]:
                elem = soup.find("meta", property=prop) or soup.find(attrs={"itemprop": prop})
                if elem:
                    return elem.get("content") or elem.get_text(strip=True)
            
            # Try time element
            time_elem = soup.find("time", attrs={"datetime": True})
            if time_elem:
                return time_elem["datetime"]
        
        elif date_type == "modified":
            for prop in ["article:modified_time", "dateModified"]:
                elem = soup.find("meta", property=prop) or soup.find(attrs={"itemprop": prop})
                if elem:
                    return elem.get("content") or elem.get_text(strip=True)
        
        return None
    
    def _remove_noise(self, soup: "BeautifulSoup") -> "BeautifulSoup":
        """Remove noisy elements from soup."""
        # Remove script, style, etc.
        for tag in self.NOISE_TAGS:
            for elem in soup.find_all(tag):
                elem.decompose()
        
        # Remove elements with noisy class/id names
        for elem in soup.find_all(True):
            classes = elem.get("class", [])
            if isinstance(classes, list):
                classes = " ".join(classes)
            elem_id = elem.get("id", "")
            
            combined = f"{classes} {elem_id}".lower()
            if any(noise in combined for noise in self.NOISE_INDICATORS):
                elem.decompose()
        
        return soup
    
    def _extract_main_content(self, soup: "BeautifulSoup") -> str:
        """Extract main content area."""
        # Try to find article or main tag
        main = soup.find("article") or soup.find("main")
        if main:
            return main.get_text(separator=" ", strip=True)[:self.max_content_length]
        
        # Score divs by content likelihood
        best_elem = None
        best_score = 0
        
        for tag in self.CONTENT_TAGS:
            for elem in soup.find_all(tag):
                score = self._score_content_element(elem)
                if score > best_score:
                    best_score = score
                    best_elem = elem
        
        if best_elem:
            return best_elem.get_text(separator=" ", strip=True)[:self.max_content_length]
        
        # Fallback to body
        body = soup.find("body")
        if body:
            return body.get_text(separator=" ", strip=True)[:self.max_content_length]
        
        return ""
    
    def _score_content_element(self, elem) -> float:
        """Score an element for likelihood of containing main content."""
        score = 0.0
        
        # Check class/id for content indicators
        classes = elem.get("class", [])
        if isinstance(classes, list):
            classes = " ".join(classes)
        elem_id = elem.get("id", "")
        combined = f"{classes} {elem_id}".lower()
        
        for indicator in self.CONTENT_INDICATORS:
            if indicator in combined:
                score += 10
        
        for indicator in self.NOISE_INDICATORS:
            if indicator in combined:
                score -= 20
        
        # Count paragraphs (more = likely content)
        p_count = len(elem.find_all("p"))
        score += p_count * 2
        
        # Text length (longer = likely content)
        text_len = len(elem.get_text())
        score += min(text_len / 100, 50)
        
        return score
    
    def _extract_text(self, soup: "BeautifulSoup") -> str:
        """Extract all text content."""
        text = soup.get_text(separator=" ", strip=True)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text[:self.max_content_length]
    
    def _extract_headings(self, soup: "BeautifulSoup") -> List[Dict[str, str]]:
        """Extract all headings."""
        headings = []
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                text = h.get_text(strip=True)
                if text:
                    headings.append({"level": f"h{level}", "text": text})
        return headings
    
    def _extract_paragraphs(self, soup: "BeautifulSoup") -> List[str]:
        """Extract paragraphs."""
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter very short paragraphs
                paragraphs.append(text)
        return paragraphs
    
    def _extract_lists(self, soup: "BeautifulSoup") -> List[List[str]]:
        """Extract lists."""
        lists = []
        for ul in soup.find_all(["ul", "ol"]):
            items = []
            for li in ul.find_all("li", recursive=False):
                text = li.get_text(strip=True)
                if text:
                    items.append(text)
            if items:
                lists.append(items)
        return lists
    
    def _extract_images(self, soup: "BeautifulSoup") -> List[Dict[str, str]]:
        """Extract image information."""
        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src", "")
            if src:
                images.append({
                    "src": src,
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                })
        return images
    
    def _extract_links(self, soup: "BeautifulSoup", base_url: str) -> tuple[List[str], List[str]]:
        """Extract internal and external links from the page."""
        from urllib.parse import urljoin, urlparse
        
        internal_links = []
        external_links = []
        seen = set()
        
        base_domain = urlparse(base_url).netloc if base_url else ""
        
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Skip duplicates
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            
            # Classify as internal or external
            link_domain = urlparse(absolute_url).netloc
            if link_domain == base_domain or (not link_domain and base_domain):
                internal_links.append(absolute_url)
            else:
                external_links.append(absolute_url)
        
        return internal_links, external_links
    
    def extract_text_only(self, html: str) -> str:
        """
        Quick method to extract just the text content.
        
        Args:
            html: HTML content
            
        Returns:
            Cleaned text content
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            if self.remove_noise:
                soup = self._remove_noise(soup)
            
            return self._extract_text(soup)
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            # Fallback: strip tags with regex
            text = re.sub(r'<[^>]+>', ' ', html)
            text = unescape(text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()[:self.max_content_length]
