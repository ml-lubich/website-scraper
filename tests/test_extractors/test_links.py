"""Tests for link extractor."""

import pytest

from website_scraper.extractors.links import LinkExtractor, LinkInfo


class TestLinkInfo:
    """Tests for LinkInfo dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        link = LinkInfo(url="https://example.com", text="Example")
        
        assert link.url == "https://example.com"
        assert link.text == "Example"
        assert link.is_internal is True
        assert link.is_navigation is False
        assert link.link_type == "content"
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        link = LinkInfo(
            url="https://example.com/page",
            text="Example Page",
            is_internal=True,
            link_type="content",
        )
        
        result = link.to_dict()
        
        assert result["url"] == "https://example.com/page"
        assert result["text"] == "Example Page"
        assert result["is_internal"] is True


class TestLinkExtractor:
    """Tests for LinkExtractor class."""
    
    def test_default_init(self):
        """Test default initialization."""
        extractor = LinkExtractor("https://example.com")
        
        assert extractor.base_url == "https://example.com"
        assert extractor.base_domain == "example.com"
        assert extractor.strip_tracking_params is True
        assert extractor.include_fragments is False
    
    def test_custom_init(self):
        """Test custom initialization."""
        extractor = LinkExtractor(
            "https://example.com",
            strip_tracking_params=False,
            include_fragments=True,
        )
        
        assert extractor.base_url == "https://example.com"
        assert extractor.strip_tracking_params is False
        assert extractor.include_fragments is True
    
    def test_extract_basic_links(self, sample_html):
        """Test basic link extraction."""
        extractor = LinkExtractor("https://example.com")
        
        links = extractor.extract(sample_html)
        
        assert len(links) > 0
        
        # Check for internal links
        urls = [link.url for link in links]
        assert any("example.com" in url for url in urls)
    
    def test_extract_detects_internal_links(self, sample_html):
        """Test internal link detection."""
        extractor = LinkExtractor("https://example.com")
        
        links = extractor.extract(sample_html)
        
        internal_links = [l for l in links if l.is_internal]
        assert len(internal_links) > 0
    
    def test_extract_detects_resource_links(self):
        """Test resource link detection."""
        html = """
        <html><body>
            <a href="https://example.com/file.pdf">PDF</a>
            <a href="https://example.com/image.jpg">Image</a>
            <a href="https://example.com/page">Page</a>
        </body></html>
        """
        
        extractor = LinkExtractor("https://example.com")
        links = extractor.extract(html)
        
        resource_links = [l for l in links if l.is_resource]
        assert len(resource_links) >= 2
    
    def test_extract_classifies_navigation(self):
        """Test navigation link classification."""
        html = """
        <html><body>
            <a href="https://example.com/login">Login</a>
            <a href="https://example.com/signup">Sign Up</a>
            <a href="https://example.com/article">Article</a>
        </body></html>
        """
        
        extractor = LinkExtractor("https://example.com")
        links = extractor.extract(html)
        
        nav_links = [l for l in links if l.link_type == "navigation" or l.is_navigation]
        content_links = [l for l in links if l.link_type == "content"]
        
        assert len(nav_links) >= 1
        assert len(content_links) >= 1

