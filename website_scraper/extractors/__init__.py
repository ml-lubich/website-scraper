"""Content and link extraction utilities."""

try:
    from .content import ContentExtractor, ExtractedPageData
    from .links import LinkExtractor, LinkInfo
except ImportError:
    # Handle missing dependencies gracefully
    ContentExtractor = None
    ExtractedPageData = None
    LinkExtractor = None
    LinkInfo = None

__all__ = [
    "ContentExtractor",
    "ExtractedPageData",
    "LinkExtractor",
    "LinkInfo",
]

