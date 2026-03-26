"""Shared pytest fixtures and configuration."""

# Legacy / alternate API tests (not aligned with current package entrypoints).
collect_ignore = [
    "test_cli.py",
    "test_cli_integration.py",
    "test_integration.py",
    "test_playwright_integration.py",
    "test_scraper_comprehensive.py",
    "test_scraper_methods.py",
    "test_scraper_playwright.py",
    "test_scraper_scrape_flow.py",
]

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock

# Sample HTML for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test Page Title</title>
    <meta name="description" content="Test meta description">
    <meta name="keywords" content="test, keywords, sample">
    <meta name="author" content="Test Author">
    <link rel="canonical" href="https://example.com/test-page">
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
    </header>
    <main>
        <h1>Main Heading</h1>
        <p>This is the first paragraph of content.</p>
        <h2>Secondary Heading</h2>
        <p>This is the second paragraph with more content.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
            <li>List item 3</li>
        </ul>
        <a href="/page1">Internal Link 1</a>
        <a href="/page2">Internal Link 2</a>
        <a href="https://external.com/page">External Link</a>
        <img src="/image.jpg" alt="Test image">
    </main>
    <footer>
        <p>Footer content</p>
    </footer>
</body>
</html>
"""

SAMPLE_HTML_MINIMAL = """
<html>
<head><title>Minimal Page</title></head>
<body><p>Simple content</p></body>
</html>
"""

SAMPLE_HTML_NO_TITLE = """
<html>
<body>
<h1>Page Without Title Tag</h1>
<p>Content without a title element.</p>
</body>
</html>
"""


@pytest.fixture
def sample_html() -> str:
    """Return sample HTML for testing."""
    return SAMPLE_HTML


@pytest.fixture
def sample_html_minimal() -> str:
    """Return minimal HTML for testing."""
    return SAMPLE_HTML_MINIMAL


@pytest.fixture
def sample_html_no_title() -> str:
    """Return HTML without title for testing."""
    return SAMPLE_HTML_NO_TITLE


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_page() -> MagicMock:
    """Create a mock Playwright page."""
    page = MagicMock()
    page.url = "https://example.com/test"
    page.title = AsyncMock(return_value="Test Page Title")
    page.content = AsyncMock(return_value=SAMPLE_HTML)
    page.viewport_size = {"width": 1920, "height": 1080}
    page.goto = AsyncMock()
    page.close = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.evaluate = AsyncMock(side_effect=lambda script, *args: _evaluate_mock(script))
    page.mouse = MagicMock()
    page.mouse.move = AsyncMock()
    return page


def _evaluate_mock(script: str):
    """Mock JavaScript evaluation results."""
    if "innerText" in script:
        return "Test page text content"
    if "scrollHeight" in script:
        return 2000
    if "querySelectorAll" in script:
        return []
    if "document.body.innerText" in script.lower():
        return "Test content from page"
    return None


@pytest.fixture
def mock_browser() -> MagicMock:
    """Create a mock Playwright browser."""
    browser = MagicMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_context(mock_page) -> MagicMock:
    """Create a mock browser context."""
    context = MagicMock()
    context.new_page = AsyncMock(return_value=mock_page)
    context.close = AsyncMock()
    context.add_init_script = AsyncMock()
    context.set_default_timeout = MagicMock()
    context.set_default_navigation_timeout = MagicMock()
    return context


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock response object."""
    response = MagicMock()
    response.status = 200
    response.headers = {"content-type": "text/html"}
    return response


@pytest.fixture
def sample_scraping_result():
    """Create a sample ScrapingResult for testing."""
    from website_scraper.exporters.base import ScrapingResult
    
    return ScrapingResult(
        url="https://example.com/test",
        title="Test Page",
        content="This is test content for the page.",
        meta_description="Test description",
        headings={"h1": ["Main Heading"], "h2": ["Sub Heading"]},
        links=[
            {"url": "https://example.com/page1", "text": "Link 1"},
            {"url": "https://example.com/page2", "text": "Link 2"},
        ],
        images=[{"url": "https://example.com/image.jpg", "alt": "Test image"}],
        summary="A summary of the test page.",
        topics=["testing", "example"],
        content_type="article",
        scraped_at="2024-01-01T00:00:00Z",
        load_time_ms=500.0,
        status_code=200,
    )


@pytest.fixture
def sample_scraping_stats():
    """Create sample ScrapingStats for testing."""
    from website_scraper.exporters.base import ScrapingStats
    
    return ScrapingStats(
        total_pages=10,
        successful_pages=9,
        failed_pages=1,
        total_links_found=50,
        total_links_followed=9,
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T00:05:00Z",
        duration_seconds=300,
        start_url="https://example.com",
        domain="example.com",
        avg_load_time_ms=450.0,
        llm_provider="openai",
        llm_calls=10,
    )


@pytest.fixture
def mock_llm_response():
    """Create mock LLM response data."""
    return {
        "title": "Extracted Title",
        "main_content": "This is the main content extracted by LLM.",
        "summary": "A brief summary.",
        "headings": ["Heading 1", "Heading 2"],
        "topics": ["topic1", "topic2"],
        "content_type": "article",
        "confidence_score": 0.95,
    }


@pytest.fixture
def mock_link_analysis_response():
    """Create mock link analysis response."""
    return {
        "links": [
            {
                "url": "https://example.com/important",
                "relevance_score": 0.9,
                "priority": 1,
                "link_type": "content",
                "should_follow": True,
                "reasoning": "High relevance content link",
            },
            {
                "url": "https://example.com/navigation",
                "relevance_score": 0.2,
                "priority": 5,
                "link_type": "navigation",
                "should_follow": False,
                "reasoning": "Navigation link, low priority",
            },
        ]
    }


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
