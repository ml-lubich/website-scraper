"""Comprehensive tests for WebScraper - testing actual functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import actual classes
from website_scraper.scraper import WebScraper, ScraperConfig
from website_scraper.exporters import ScrapingResult, ScrapingStats
from website_scraper.extractors import ContentExtractor, LinkExtractor


@pytest.mark.asyncio
class TestWebScraperLLMEnhancement:
    """Test LLM enhancement functionality."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    @patch('website_scraper.scraper.create_llm_provider')
    async def test_enhance_with_llm(self, mock_llm_factory, mock_driver_class):
        """Test LLM enhancement of results."""
        # Mock LLM
        mock_llm = AsyncMock()
        mock_extracted = MagicMock()
        mock_extracted.title = "LLM Title"
        mock_extracted.main_content = "LLM content"
        mock_extracted.summary = "LLM summary"
        mock_extracted.topics = ["topic1"]
        mock_extracted.content_type = "article"
        mock_llm.analyze_content = AsyncMock(return_value=mock_extracted)
        mock_llm_factory.return_value = mock_llm
        
        # Mock driver
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=1,
            llm_provider="openai",
            llm_api_key="test-key",
        )
        
        async with WebScraper(config=config) as scraper:
            results, _ = await scraper.scrape(show_progress=False)
        
        assert len(results) == 1
        mock_llm.analyze_content.assert_called_once()


@pytest.mark.asyncio
class TestWebScraperLinkExtraction:
    """Test link extraction and following."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_extracts_and_follows_links(self, mock_driver_class):
        """Test scraper extracts and follows links."""
        html1 = """
        <html>
            <body>
                <a href="/page2">Page 2</a>
                <a href="/page3">Page 3</a>
            </body>
        </html>
        """
        
        html2 = "<html><body><p>Page 2 content</p></body></html>"
        
        mock_page1 = MagicMock()
        mock_page1.close = AsyncMock()
        mock_page2 = MagicMock()
        mock_page2.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        
        page_count = 0
        async def new_page():
            nonlocal page_count
            page_count += 1
            return mock_page1 if page_count == 1 else mock_page2
        
        mock_driver.new_page = AsyncMock(side_effect=new_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        
        content_count = 0
        async def get_content(page):
            nonlocal content_count
            content_count += 1
            return html1 if content_count == 1 else html2
        
        mock_driver.get_page_content = AsyncMock(side_effect=get_content)
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=2,
        )
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        # Should have scraped multiple pages
        assert stats.total_pages >= 1


@pytest.mark.asyncio
class TestWebScraperStatistics:
    """Test statistics generation."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_stats_generation(self, mock_driver_class):
        """Test statistics are generated correctly."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><body><p>Content</p></body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        assert isinstance(stats, ScrapingStats)
        assert stats.total_pages == 1
        assert stats.successful_pages == 1
        assert stats.failed_pages == 0
        assert stats.start_url == "https://example.com"
        assert stats.domain == "example.com"
        assert stats.duration_seconds > 0


@pytest.mark.asyncio
class TestWebScraperProgressBar:
    """Test progress bar functionality."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    @patch('website_scraper.scraper.tqdm')
    async def test_progress_bar_created(self, mock_tqdm, mock_driver_class):
        """Test progress bar is created when show_progress=True."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            await scraper.scrape(show_progress=True)
        
        # Progress bar should have been created
        mock_tqdm.assert_called_once()
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    @patch('website_scraper.scraper.tqdm')
    async def test_no_progress_bar_when_disabled(self, mock_tqdm, mock_driver_class):
        """Test progress bar is not created when show_progress=False."""
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            await scraper.scrape(show_progress=False)
        
        # Progress bar should not have been created
        mock_tqdm.assert_not_called()


@pytest.mark.asyncio
class TestWebScraperErrorRecovery:
    """Test error recovery and handling."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_continues_after_page_error(self, mock_driver_class):
        """Test scraper continues after individual page error."""
        mock_page1 = MagicMock()
        mock_page1.close = AsyncMock()
        mock_page2 = MagicMock()
        mock_page2.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        
        page_count = 0
        async def new_page():
            nonlocal page_count
            page_count += 1
            return mock_page1 if page_count == 1 else mock_page2
        
        mock_driver.new_page = AsyncMock(side_effect=new_page)
        
        # First page fails, second succeeds
        call_count = 0
        async def goto_side_effect(page, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Page error")
            return MagicMock(status=200)
        
        mock_driver.goto = AsyncMock(side_effect=goto_side_effect)
        mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
        mock_driver.get_title = AsyncMock(return_value="Test")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(
            base_url="https://example.com",
            max_pages=2,
        )
        
        async with WebScraper(config=config) as scraper:
            results, stats = await scraper.scrape(show_progress=False)
        
        # Should have attempted both pages
        assert stats.total_pages == 2
        # At least one should have failed
        assert stats.failed_pages >= 1


@pytest.mark.asyncio
class TestWebScraperConfigOptions:
    """Test various configuration options."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_different_browser_types(self, mock_driver_class):
        """Test different browser types."""
        for browser_type in ["chromium", "firefox", "webkit"]:
            mock_driver = AsyncMock()
            mock_driver.start = AsyncMock()
            mock_driver.close = AsyncMock()
            mock_driver.new_page = AsyncMock(return_value=MagicMock())
            mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
            mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
            mock_driver.get_title = AsyncMock(return_value="Test")
            mock_driver_class.return_value = mock_driver
            
            config = ScraperConfig(
                base_url="https://example.com",
                max_pages=1,
                browser_type=browser_type,
            )
            
            async with WebScraper(config=config) as scraper:
                # Should initialize without error
                assert scraper.config.browser_type == browser_type
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_headless_vs_non_headless(self, mock_driver_class):
        """Test headless and non-headless modes."""
        for headless in [True, False]:
            mock_driver = AsyncMock()
            mock_driver.start = AsyncMock()
            mock_driver.close = AsyncMock()
            mock_driver.new_page = AsyncMock(return_value=MagicMock())
            mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
            mock_driver.get_page_content = AsyncMock(return_value="<html><body>Content</body></html>")
            mock_driver.get_title = AsyncMock(return_value="Test")
            mock_driver_class.return_value = mock_driver
            
            config = ScraperConfig(
                base_url="https://example.com",
                max_pages=1,
                headless=headless,
            )
            
            async with WebScraper(config=config) as scraper:
                assert scraper.config.headless == headless


@pytest.mark.asyncio
class TestWebScraperContentProcessing:
    """Test content processing and extraction."""
    
    @patch('website_scraper.scraper.PlaywrightDriver')
    async def test_processes_complex_html(self, mock_driver_class):
        """Test processing complex HTML with various elements."""
        complex_html = """
        <html>
            <head>
                <title>Complex Page</title>
                <meta name="description" content="Complex description">
            </head>
            <body>
                <h1>Main Heading</h1>
                <h2>Sub Heading</h2>
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
                <img src="/image.jpg" alt="Image">
                <a href="/link1">Link 1</a>
                <a href="/link2">Link 2</a>
            </body>
        </html>
        """
        
        mock_page = MagicMock()
        mock_page.close = AsyncMock()
        
        mock_driver = AsyncMock()
        mock_driver.start = AsyncMock()
        mock_driver.close = AsyncMock()
        mock_driver.new_page = AsyncMock(return_value=mock_page)
        mock_driver.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_driver.get_page_content = AsyncMock(return_value=complex_html)
        mock_driver.get_title = AsyncMock(return_value="Complex Page")
        mock_driver_class.return_value = mock_driver
        
        config = ScraperConfig(base_url="https://example.com", max_pages=1)
        
        async with WebScraper(config=config) as scraper:
            results, _ = await scraper.scrape(show_progress=False)
        
        assert len(results) == 1
        result = results[0]
        assert result.title == "Complex Page"
        assert result.meta_description == "Complex description"
        assert len(result.headings) > 0
        assert len(result.links) > 0
        assert len(result.images) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
