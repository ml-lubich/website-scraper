import unittest
import sys
import types
from unittest.mock import patch, MagicMock
from website_scraper import WebScraper
from pathlib import Path
import tempfile
import shutil
import requests
import os
import time

class TestWebScraper(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for logs
        self.test_dir = tempfile.mkdtemp()
        self.scraper = WebScraper(
            base_url="https://example.com",
            log_dir=self.test_dir
        )

    def tearDown(self):
        # Close all log handlers before cleanup
        if hasattr(self, 'scraper') and self.scraper:
            if hasattr(self.scraper, 'logger') and self.scraper.logger:
                for handler in self.scraper.logger.handlers:
                    handler.close()
                self.scraper.logger.handlers.clear()
        
        # Wait a moment to ensure files are closed
        time.sleep(0.1)
        
        # Clean up the temporary directory
        for retry in range(3):
            try:
                if os.path.exists(self.test_dir):
                    shutil.rmtree(self.test_dir)
                break
            except Exception:
                if retry < 2:  # Don't sleep on last attempt
                    time.sleep(0.1 * (retry + 1))
                continue

    def test_initialization(self):
        """Test scraper initialization"""
        self.assertEqual(self.scraper.base_url, "https://example.com")
        self.assertEqual(self.scraper.delay_range, (1, 3))
        self.assertEqual(self.scraper.max_retries, 3)
        self.assertTrue(Path(self.test_dir).exists())

    @patch('requests.Session')
    def test_make_request(self, mock_session):
        """Test request making with mocked session"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_session.return_value.get.return_value = mock_response

        # Make request
        response = self.scraper._make_request("https://example.com", mock_session())
        
        # Verify response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)

    @patch('requests.Session')
    def test_failed_request(self, mock_session):
        """Test failed request handling"""
        # Setup mock session to raise an exception
        mock_session.return_value.get.side_effect = requests.exceptions.RequestException("Connection failed")

        # Make request
        response = self.scraper._make_request("https://example.com", mock_session())
        
        # Verify response is None for failed request
        self.assertIsNone(response)

    def test_extract_links(self):
        """Test link extraction from HTML"""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <body>
                <a href="https://example.com/page1">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="https://other-domain.com">External</a>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        links = self.scraper._extract_links(soup, "https://example.com")
        
        # Should find 2 links (one absolute, one relative, excluding external)
        self.assertEqual(len(links), 2)
        self.assertIn("https://example.com/page1", links)
        self.assertIn("https://example.com/page2", links)

    def test_extract_data(self):
        """Test data extraction from HTML"""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test Description">
            </head>
            <body>
                <p>Test Content</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        data = self.scraper._extract_data(soup)
        
        self.assertEqual(data['title'], "Test Page")
        self.assertEqual(data['meta_description'], "Test Description")
        self.assertIn("Test Content", data['text'])

    def test_undetected_chrome_raises_without_dependency(self):
        with patch("website_scraper.scraper.importlib.util.find_spec", return_value=None):
            scraper = WebScraper(
                "https://example.com",
                log_dir=self.test_dir,
                use_undetected_chrome=True,
            )
            with self.assertRaises(ImportError) as ctx:
                scraper.scrape(show_progress=False)
            self.assertIn("undetected", str(ctx.exception).lower())

    def test_undetected_chrome_scrape_with_fake_module(self):
        mock_driver = MagicMock()
        mock_driver.page_source = (
            "<html><head><title>UC</title></head><body><p>x</p></body></html>"
        )
        fake = types.ModuleType("undetected_chromedriver")
        fake.ChromeOptions = MagicMock(return_value=MagicMock())
        fake.Chrome = MagicMock(return_value=mock_driver)
        sys.modules["undetected_chromedriver"] = fake
        try:
            with patch(
                "website_scraper.scraper.importlib.util.find_spec",
                return_value=MagicMock(),
            ):
                scraper = WebScraper(
                    "https://example.com",
                    log_dir=self.test_dir,
                    use_undetected_chrome=True,
                )
                data, stats = scraper.scrape(show_progress=False)
            self.assertEqual(stats.get("fetch_mode"), "undetected_chrome")
            self.assertIn("https://example.com", data)
            self.assertEqual(data["https://example.com"].get("title"), "UC")
            mock_driver.quit.assert_called()
        finally:
            sys.modules.pop("undetected_chromedriver", None)


if __name__ == '__main__':
    unittest.main() 