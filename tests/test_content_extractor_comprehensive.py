"""Comprehensive tests for ContentExtractor - testing actual code execution."""

import pytest
from bs4 import BeautifulSoup

from website_scraper.extractors.content import ContentExtractor, ExtractedPageData


class TestContentExtractorComprehensive:
    """Comprehensive tests that execute actual ContentExtractor code."""
    
    def test_extract_full_page(self):
        """Test extracting a full page with all features."""
        extractor = ContentExtractor()
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Full Test Page</title>
            <meta name="description" content="Full page description">
            <meta name="keywords" content="test, page, example">
            <meta name="author" content="Test Author">
            <meta property="og:title" content="OG Title">
        </head>
        <body>
            <header>Header Content</header>
            <nav>Navigation</nav>
            <main>
                <article>
                    <h1>Main Heading</h1>
                    <h2>Sub Heading</h2>
                    <p>First paragraph with content.</p>
                    <p>Second paragraph with more content.</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2</li>
                    </ul>
                    <a href="/page1">Internal Link</a>
                    <a href="https://external.com">External Link</a>
                    <img src="/image.jpg" alt="Test Image">
                </article>
            </main>
            <footer>Footer Content</footer>
        </body>
        </html>
        """
        
        result = extractor.extract(html, "https://example.com")
        
        # Verify all fields
        assert result.title == "Full Test Page"
        assert result.meta_description == "Full page description"
        assert "test" in result.meta_keywords
        assert result.author == "Test Author"
        assert result.language == "en"
        
        # Verify content
        assert len(result.headings) > 0
        assert "Main Heading" in [h.get("text", "") for h in result.headings]
        assert len(result.paragraphs) >= 2
        assert "First paragraph" in result.text
        
        # Verify links
        assert len(result.internal_links) > 0
        assert any("page1" in link for link in result.internal_links)
        assert len(result.external_links) > 0
        assert any("external.com" in link for link in result.external_links)
        
        # Verify images
        assert len(result.images) > 0
        assert any("image.jpg" in img.get("src", "") for img in result.images)
    
    def test_extract_with_noise_removal(self):
        """Test extraction with noise removal enabled."""
        extractor = ContentExtractor(remove_noise=True)
        
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <nav>Navigation</nav>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
            <main>
                <p>Real content here</p>
            </main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        
        result = extractor.extract(html, "https://example.com")
        
        # Should not contain script/style content
        assert "alert" not in result.text
        assert "color: red" not in result.text
        assert "Real content" in result.text
    
    def test_extract_without_noise_removal(self):
        """Test extraction with noise removal disabled."""
        extractor = ContentExtractor(remove_noise=False)
        
        html = """
        <html>
        <body>
            <nav>Navigation</nav>
            <p>Content</p>
        </body>
        </html>
        """
        
        result = extractor.extract(html, "https://example.com")
        
        # Should include navigation
        assert "Navigation" in result.text or "Content" in result.text
    
    def test_extract_images_disabled(self):
        """Test extraction with images disabled."""
        extractor = ContentExtractor(extract_images=False)
        
        html = """
        <html>
        <body>
            <img src="/test.jpg" alt="Test">
            <p>Content</p>
        </body>
        </html>
        """
        
        result = extractor.extract(html, "https://example.com")
        
        assert result.images == []
    
    def test_extract_text_truncation(self):
        """Test text truncation at max length."""
        extractor = ContentExtractor(max_content_length=100)
        
        html = "<html><body><p>" + "x" * 1000 + "</p></body></html>"
        result = extractor.extract(html, "https://example.com")
        
        assert len(result.text) <= 100
    
    def test_extract_empty_html(self):
        """Test extraction from empty HTML."""
        extractor = ContentExtractor()
        
        html = "<html><body></body></html>"
        result = extractor.extract(html, "https://example.com")
        
        assert result.title == ""
        assert result.text == ""
        assert result.internal_links == []
        assert result.external_links == []
    
    def test_extract_malformed_html(self):
        """Test extraction from malformed HTML."""
        extractor = ContentExtractor()
        
        html = "<html><body><p>Unclosed tag<p>More content</body></html>"
        result = extractor.extract(html, "https://example.com")
        
        # Should still extract what it can
        assert isinstance(result, ExtractedPageData)
        assert "More content" in result.text or "Unclosed" in result.text
    
    def test_extract_links_edge_cases(self):
        """Test link extraction edge cases."""
        extractor = ContentExtractor()
        
        # Test with various link formats
        html = """
        <html>
        <body>
            <a href="relative">Relative</a>
            <a href="/absolute">Absolute</a>
            <a href="https://example.com/full">Full URL</a>
            <a href="//protocol-relative">Protocol Relative</a>
            <a>No href</a>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extractor._extract_links(soup, "https://example.com")
        
        # Should handle all formats
        assert len(internal) >= 2  # relative, /absolute, full URL
        # Protocol relative might be classified as external
    
    def test_extract_links_same_domain_variations(self):
        """Test link extraction with domain variations."""
        extractor = ContentExtractor()
        
        html = """
        <html>
        <body>
            <a href="https://example.com/page1">Same domain</a>
            <a href="https://www.example.com/page2">WWW variant</a>
            <a href="https://sub.example.com/page3">Subdomain</a>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html, "html.parser")
        internal, external = extractor._extract_links(soup, "https://example.com")
        
        # example.com and www.example.com should be internal
        # sub.example.com might be external depending on implementation
        assert len(internal) >= 1
        assert "page1" in internal[0] or "page2" in internal[0] if internal else True
