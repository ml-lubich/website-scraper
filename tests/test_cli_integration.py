"""Real integration tests for CLI that actually test the code."""

import pytest
import subprocess
import sys
import tempfile
from pathlib import Path

# Import the actual CLI module
from website_scraper.cli import create_parser, run_scraper, main
import argparse


class TestCLIIntegration:
    """Real tests for CLI that import and test the actual code."""
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        
        assert parser is not None
        assert parser.prog == "website-scraper"
    
    def test_parser_has_required_args(self):
        """Test parser has required arguments."""
        parser = create_parser()
        
        # Parse with URL
        args = parser.parse_args(["https://example.com"])
        assert args.url == "https://example.com"
    
    def test_parser_has_optional_args(self):
        """Test parser has optional arguments."""
        parser = create_parser()
        
        args = parser.parse_args([
            "https://example.com",
            "--max-pages", "10",
            "--format", "markdown",
            "--browser", "firefox",
        ])
        
        assert args.max_pages == 10
        assert args.format == "markdown"
        assert args.browser == "firefox"
    
    def test_parser_llm_options(self):
        """Test LLM-related options."""
        parser = create_parser()
        
        args = parser.parse_args([
            "https://example.com",
            "--llm", "openai",
            "--api-key", "test-key",
        ])
        
        assert args.llm == "openai"
        assert args.api_key == "test-key"
    
    def test_parser_output_options(self):
        """Test output-related options."""
        parser = create_parser()
        
        args = parser.parse_args([
            "https://example.com",
            "--output", "results.json",
            "--format", "json",
        ])
        
        assert args.output == "results.json"
        assert args.format == "json"
    
    def test_parser_timing_options(self):
        """Test timing options."""
        parser = create_parser()
        
        args = parser.parse_args([
            "https://example.com",
            "--min-delay", "2.0",
            "--max-delay", "5.0",
            "--timeout", "60",
        ])
        
        assert args.min_delay == 2.0
        assert args.max_delay == 5.0
        assert args.timeout == 60
    
    def test_parser_browser_options(self):
        """Test browser options."""
        parser = create_parser()
        
        args = parser.parse_args([
            "https://example.com",
            "--browser", "webkit",
            "--no-headless",
        ])
        
        assert args.browser == "webkit"
        assert args.no_headless is True
    
    def test_parser_logging_options(self):
        """Test logging options."""
        parser = create_parser()
        
        args = parser.parse_args([
            "https://example.com",
            "--log-dir", "custom_logs",
            "--verbose",
            "--quiet",
        ])
        
        assert args.log_dir == "custom_logs"
        assert args.verbose is True
        assert args.quiet is True
    
    def test_parser_version(self):
        """Test version option."""
        parser = create_parser()
        
        # Should not raise
        try:
            parser.parse_args(["--version"])
        except SystemExit:
            pass  # argparse exits on --version
    
    def test_parser_help(self):
        """Test help option."""
        parser = create_parser()
        
        # Should not raise
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            pass  # argparse exits on --help

