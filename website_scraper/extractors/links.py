"""Link extraction utilities for web pages."""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs

logger = logging.getLogger(__name__)


@dataclass
class LinkInfo:
    """Information about an extracted link."""
    
    url: str
    text: str
    title: str = ""
    
    # Classification
    is_internal: bool = True
    is_navigation: bool = False
    is_resource: bool = False  # CSS, JS, image, etc.
    link_type: str = "content"  # content, navigation, social, download, etc.
    follow: bool = True  # Whether crawlers should enqueue this link
    
    # Additional context
    rel: str = ""
    target: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "text": self.text,
            "title": self.title,
            "is_internal": self.is_internal,
            "is_navigation": self.is_navigation,
            "is_resource": self.is_resource,
            "link_type": self.link_type,
        }


class LinkExtractor:
    """
    Extracts and classifies links from HTML pages.
    
    Provides methods for extracting all links, filtering by type,
    and normalizing URLs.
    """
    
    # File extensions that indicate resources
    RESOURCE_EXTENSIONS = {
        ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".webp", ".ico", ".woff", ".woff2", ".ttf", ".eot",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip",
        ".mp3", ".mp4", ".avi", ".mov", ".wav",
    }
    
    # Social media domains
    SOCIAL_DOMAINS = {
        "facebook.com", "twitter.com", "x.com", "instagram.com",
        "linkedin.com", "youtube.com", "tiktok.com", "pinterest.com",
        "reddit.com", "whatsapp.com", "t.me", "telegram.org",
    }
    
    # Navigation indicators in URL or link text
    NAV_INDICATORS = {
        "login", "signin", "signup", "register", "logout",
        "cart", "checkout", "account", "profile", "settings",
        "privacy", "terms", "contact", "about", "faq", "help",
        "search", "sitemap", "subscribe", "newsletter",
    }
    
    # Parameters to strip from URLs
    STRIP_PARAMS = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "ref", "source", "fbclid", "gclid", "mc_cid", "mc_eid",
    }
    
    def __init__(
        self,
        base_url: str,
        strip_tracking_params: bool = True,
        include_fragments: bool = False,
    ):
        """
        Initialize the link extractor.
        
        Args:
            base_url: Base URL for determining internal links
            strip_tracking_params: Whether to remove tracking parameters
            include_fragments: Whether to include URL fragments (#section)
        """
        self.base_url = base_url
        self.strip_tracking_params = strip_tracking_params
        self.include_fragments = include_fragments
        
        # Parse base URL
        parsed = urlparse(base_url)
        self.base_domain = parsed.netloc.lower()
        self.base_scheme = parsed.scheme
    
    def extract(self, html: str, current_url: Optional[str] = None) -> List[LinkInfo]:
        """
        Extract all links from HTML.
        
        Args:
            html: HTML content string
            current_url: Current page URL (for resolving relative links)
            
        Returns:
            List of LinkInfo objects
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup not installed")
            return []
        
        current_url = current_url or self.base_url
        links: List[LinkInfo] = []
        seen_urls: Set[str] = set()
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            for anchor in soup.find_all("a", href=True):
                href = anchor.get("href", "").strip()
                
                if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                    continue
                
                # Resolve relative URL
                absolute_url = urljoin(current_url, href)
                
                # Normalize URL
                normalized_url = self._normalize_url(absolute_url)
                
                if not normalized_url or normalized_url in seen_urls:
                    continue
                
                seen_urls.add(normalized_url)
                
                # Extract link info
                link_info = self._create_link_info(
                    anchor=anchor,
                    url=normalized_url,
                )
                
                links.append(link_info)
            
            return links
            
        except Exception as e:
            logger.error(f"Link extraction failed: {e}")
            return []
    
    def extract_internal(self, html: str, current_url: Optional[str] = None) -> List[LinkInfo]:
        """
        Extract only internal links.
        
        Args:
            html: HTML content
            current_url: Current page URL
            
        Returns:
            List of internal LinkInfo objects
        """
        all_links = self.extract(html, current_url)
        return [link for link in all_links if link.is_internal]
    
    def extract_external(self, html: str, current_url: Optional[str] = None) -> List[LinkInfo]:
        """
        Extract only external links.
        
        Args:
            html: HTML content
            current_url: Current page URL
            
        Returns:
            List of external LinkInfo objects
        """
        all_links = self.extract(html, current_url)
        return [link for link in all_links if not link.is_internal]
    
    def extract_content_links(self, html: str, current_url: Optional[str] = None) -> List[LinkInfo]:
        """
        Extract links that likely point to content pages.
        
        Filters out navigation, social, and resource links.
        
        Args:
            html: HTML content
            current_url: Current page URL
            
        Returns:
            List of content LinkInfo objects
        """
        all_links = self.extract(html, current_url)
        return [
            link for link in all_links
            if link.is_internal
            and not link.is_navigation
            and not link.is_resource
            and link.link_type == "content"
        ]
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize a URL.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL or None if invalid
        """
        try:
            parsed = urlparse(url)
            
            # Only process http/https
            if parsed.scheme not in ("http", "https"):
                return None
            
            # Normalize domain
            netloc = parsed.netloc.lower()
            
            # Strip tracking parameters
            if self.strip_tracking_params:
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                filtered_params = {
                    k: v for k, v in query_params.items()
                    if k.lower() not in self.STRIP_PARAMS
                }
                # Rebuild query string
                if filtered_params:
                    query = "&".join(
                        f"{k}={v[0]}" for k, v in sorted(filtered_params.items())
                    )
                else:
                    query = ""
            else:
                query = parsed.query
            
            # Handle fragment
            fragment = parsed.fragment if self.include_fragments else ""
            
            # Normalize path
            path = parsed.path or "/"
            # Remove trailing slash except for root
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")
            
            # Rebuild URL
            normalized = urlunparse((
                parsed.scheme,
                netloc,
                path,
                parsed.params,
                query,
                fragment,
            ))
            
            return normalized
            
        except Exception as e:
            logger.debug(f"URL normalization failed for {url}: {e}")
            return None
    
    def _create_link_info(self, anchor, url: str) -> LinkInfo:
        """
        Create LinkInfo from anchor element.
        
        Args:
            anchor: BeautifulSoup anchor element
            url: Normalized URL
            
        Returns:
            LinkInfo object
        """
        # Extract text
        text = anchor.get_text(strip=True)
        if not text:
            # Try to get text from nested elements or title
            text = anchor.get("title", "") or anchor.get("aria-label", "")
        text = text[:200]  # Limit length
        
        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Determine if internal
        is_internal = self._is_internal_domain(domain)
        
        # Determine link type
        link_type = self._classify_link(url, text, domain, path)
        
        # Check if navigation
        is_navigation = self._is_navigation_link(url, text, anchor)
        
        # Check if resource
        is_resource = self._is_resource_link(url)
        
        return LinkInfo(
            url=url,
            text=text,
            title=anchor.get("title", ""),
            is_internal=is_internal,
            is_navigation=is_navigation,
            is_resource=is_resource,
            link_type=link_type,
            rel=anchor.get("rel", [""])[0] if isinstance(anchor.get("rel"), list) else anchor.get("rel", ""),
            target=anchor.get("target", ""),
        )
    
    def _is_internal_domain(self, domain: str) -> bool:
        """Check if domain is internal."""
        # Direct match
        if domain == self.base_domain:
            return True
        
        # Subdomain match (www.example.com matches example.com)
        if domain.endswith(f".{self.base_domain}"):
            return True
        
        # Handle www prefix
        if self.base_domain.startswith("www."):
            base_no_www = self.base_domain[4:]
            if domain == base_no_www or domain.endswith(f".{base_no_www}"):
                return True
        else:
            if domain == f"www.{self.base_domain}":
                return True
        
        return False
    
    def _classify_link(self, url: str, text: str, domain: str, path: str) -> str:
        """
        Classify the type of link.
        
        Args:
            url: Full URL
            text: Link text
            domain: URL domain
            path: URL path
            
        Returns:
            Link type string
        """
        # Check for social media
        for social in self.SOCIAL_DOMAINS:
            if social in domain:
                return "social"
        
        # Check for download
        ext = path.rsplit(".", 1)[-1] if "." in path else ""
        if ext in {"pdf", "doc", "docx", "xls", "xlsx", "zip", "rar"}:
            return "download"
        
        # Check for image/media
        if ext in {"jpg", "jpeg", "png", "gif", "mp4", "mp3"}:
            return "media"
        
        # Check for navigation based on path/text
        combined = f"{path} {text}".lower()
        for nav in self.NAV_INDICATORS:
            if nav in combined:
                return "navigation"
        
        return "content"
    
    def _is_navigation_link(self, url: str, text: str, anchor) -> bool:
        """Check if link is a navigation link."""
        # Check rel attribute
        rel = anchor.get("rel", [])
        if isinstance(rel, list):
            rel = " ".join(rel)
        if "nofollow" in rel.lower():
            return True
        
        # Check text and URL
        combined = f"{url} {text}".lower()
        nav_patterns = [
            r"^\s*menu\s*$",
            r"^\s*home\s*$",
            r"^\s*back\s*$",
            r"^\s*next\s*$",
            r"^\s*prev(ious)?\s*$",
        ]
        
        for pattern in nav_patterns:
            if re.search(pattern, text.lower()):
                return True
        
        # Check parent elements for nav indicators
        parent = anchor.parent
        for _ in range(3):  # Check up to 3 levels
            if parent:
                parent_classes = parent.get("class", [])
                if isinstance(parent_classes, list):
                    parent_classes = " ".join(parent_classes)
                parent_id = parent.get("id", "")
                combined_parent = f"{parent_classes} {parent_id}".lower()
                
                if any(nav in combined_parent for nav in ["nav", "menu", "header", "footer"]):
                    return True
                
                parent = parent.parent
        
        return False
    
    def _is_resource_link(self, url: str) -> bool:
        """Check if link points to a resource file."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in self.RESOURCE_EXTENSIONS:
            if path.endswith(ext):
                return True
        
        return False
    
    def get_unique_urls(self, links: List[LinkInfo]) -> List[str]:
        """
        Get unique URLs from link list.
        
        Args:
            links: List of LinkInfo objects
            
        Returns:
            List of unique URL strings
        """
        seen: Set[str] = set()
        unique: List[str] = []
        
        for link in links:
            if link.url not in seen:
                seen.add(link.url)
                unique.append(link.url)
        
        return unique
