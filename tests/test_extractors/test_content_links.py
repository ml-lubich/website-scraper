"""Real tests for content extractor link extraction."""

import pytest
from website_scraper.extractors import ContentExtractor


class TestContentExtractorLinks:
    """Real tests for link extraction in ContentExtractor."""
    
    def test_extract_links_internal_and_external(self):
        """Test extracting internal and external links."""
        html = """
        <html>
        <body>
            <a href="/internal1">Internal 1</a>
            <a href="/internal2">Internal 2</a>
            <a href="https://external.com/page">External</a>
            <a href="https://example.com/same">Same Domain</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Should have internal links
        assert len(result.internal_links) >= 2
        
        # Should have external links
        assert len(result.external_links) >= 1
        assert any("external.com" in link for link in result.external_links)
    
    def test_extract_links_skips_anchors(self):
        """Test that anchor links are skipped."""
        html = """
        <html>
        <body>
            <a href="#section">Anchor</a>
            <a href="/page">Real Link</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Should not include anchor links
        assert not any("#section" in link for link in result.internal_links + result.external_links)
        # Should include real links
        assert any("/page" in link for link in result.internal_links)
    
    def test_extract_links_skips_javascript(self):
        """Test that javascript: links are skipped."""
        html = """
        <html>
        <body>
            <a href="javascript:void(0)">JS Link</a>
            <a href="/page">Real Link</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Should not include javascript links
        assert not any("javascript:" in link for link in result.internal_links + result.external_links)
    
    def test_extract_links_skips_mailto_tel(self):
        """Test that mailto: and tel: links are skipped."""
        html = """
        <html>
        <body>
            <a href="mailto:test@example.com">Email</a>
            <a href="tel:+1234567890">Phone</a>
            <a href="/page">Real Link</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Should not include mailto/tel links
        assert not any("mailto:" in link or "tel:" in link for link in result.internal_links + result.external_links)
    
    def test_extract_links_deduplicates(self):
        """Test that duplicate links are removed."""
        html = """
        <html>
        <body>
            <a href="/page1">Link 1</a>
            <a href="/page1">Link 1 Duplicate</a>
            <a href="/page2">Link 2</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com")
        
        # Should deduplicate
        assert result.internal_links.count("https://example.com/page1") == 1
    
    def test_extract_links_resolves_relative_urls(self):
        """Test that relative URLs are resolved."""
        html = """
        <html>
        <body>
            <a href="/page1">Relative</a>
            <a href="page2">Relative 2</a>
            <a href="../page3">Parent</a>
        </body>
        </html>
        """
        
        extractor = ContentExtractor()
        result = extractor.extract(html, "https://example.com/base/")
        
        # All should be absolute URLs
        for link in result.internal_links:
            assert link.startswith("https://")
            assert "example.com" in link

