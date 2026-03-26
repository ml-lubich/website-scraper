"""Tests for content extractor."""

import pytest

from website_scraper.extractors.content import ContentExtractor, ExtractedPageData


class TestExtractedPageData:
    """Tests for ExtractedPageData dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        data = ExtractedPageData()
        
        assert data.url == ""
        assert data.title == ""
        assert data.text == ""
        assert data.internal_links == []
        assert data.external_links == []
        assert data.images == []
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        data = ExtractedPageData(
            url="https://example.com",
            title="Test Page",
            text="Test content",
            meta_description="Test description",
        )
        
        result = data.to_dict()
        
        assert result["url"] == "https://example.com"
        assert result["title"] == "Test Page"
        assert result["text"] == "Test content"


class TestContentExtractor:
    """Tests for ContentExtractor class."""
    
    def test_default_init(self):
        """Test default initialization."""
        extractor = ContentExtractor()
        
        assert extractor.remove_noise is True
        assert extractor.extract_images is True
        assert extractor.max_content_length == 100000
    
    def test_custom_init(self):
        """Test custom initialization."""
        extractor = ContentExtractor(
            remove_noise=False,
            extract_images=False,
            max_content_length=1000,
        )
        
        assert extractor.remove_noise is False
        assert extractor.extract_images is False
        assert extractor.max_content_length == 1000
    
    def test_extract_title(self, sample_html):
        """Test title extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert result.title == "Test Page Title"
    
    def test_extract_title_from_h1(self, sample_html_no_title):
        """Test title extraction from h1 when no title tag."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html_no_title, "https://example.com")
        
        assert "Page Without Title" in result.title
    
    def test_extract_meta_description(self, sample_html):
        """Test meta description extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert result.meta_description == "Test meta description"
    
    def test_extract_meta_keywords(self, sample_html):
        """Test meta keywords extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert "test" in result.meta_keywords
        assert "keywords" in result.meta_keywords
    
    def test_extract_text(self, sample_html):
        """Test text extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert "Main Heading" in result.text
        assert "first paragraph" in result.text
    
    def test_extract_headings(self, sample_html):
        """Test heading extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert len(result.headings) > 0
        # Headings are list of dicts with level and text
        heading_levels = [h.get("level") for h in result.headings]
        assert "h1" in heading_levels
    
    def test_extract_links(self, sample_html):
        """Test link extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert len(result.internal_links) > 0 or len(result.external_links) > 0
        
        # Check for internal links
        all_links = result.internal_links + result.external_links
        assert any("/page1" in url or "page1" in url for url in all_links)
    
    def test_extract_images(self, sample_html):
        """Test image extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert len(result.images) > 0
        assert any("image.jpg" in img.get("src", "") for img in result.images)
    
    def test_extract_language(self, sample_html):
        """Test language extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert result.language == "en"
    
    def test_extract_author(self, sample_html):
        """Test author extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert result.author == "Test Author"
    
    def test_skip_images_when_disabled(self, sample_html):
        """Test skipping image extraction when disabled."""
        extractor = ContentExtractor(extract_images=False)
        
        result = extractor.extract(sample_html, "https://example.com")
        
        assert result.images == []
    
    def test_clean_html_removes_scripts(self):
        """Test that scripts are removed."""
        html_with_script = """
        <html>
        <head><title>Test</title></head>
        <body>
            <script>alert('bad');</script>
            <p>Content</p>
        </body>
        </html>
        """
        
        extractor = ContentExtractor(remove_noise=True)
        result = extractor.extract(html_with_script, "https://example.com")
        
        assert "alert" not in result.text
    
    def test_text_truncation(self):
        """Test text is truncated to max length."""
        long_html = "<html><body>" + "x" * 1000000 + "</body></html>"
        
        extractor = ContentExtractor(max_content_length=1000)
        result = extractor.extract(long_html, "https://example.com")
        
        assert len(result.text) <= 1000
    
    def test_minimal_html(self, sample_html_minimal):
        """Test extraction from minimal HTML."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html_minimal, "https://example.com")
        
        assert result.title == "Minimal Page"
        assert "Simple content" in result.text
    
    def test_extract_links_integration(self, sample_html):
        """Test that extract() includes link extraction."""
        extractor = ContentExtractor()
        
        result = extractor.extract(sample_html, "https://example.com")
        
        # Verify links are extracted
        assert hasattr(result, 'internal_links')
        assert hasattr(result, 'external_links')
        assert isinstance(result.internal_links, list)
        assert isinstance(result.external_links, list)
        
        # Should have found internal links from sample HTML
        assert len(result.internal_links) > 0

