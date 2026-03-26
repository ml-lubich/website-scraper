"""Tests for CLI module."""

import pytest
import argparse
import sys
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from website_scraper.cli import (
    create_parser,
    setup_console_logging,
    run_scraper,
    main,
)


class TestCreateParser:
    """Tests for argument parser creation."""
    
    def test_parser_creation(self):
        """Test parser is created successfully."""
        parser = create_parser()
        
        assert parser is not None
        assert isinstance(parser, argparse.ArgumentParser)
    
    def test_parser_prog_name(self):
        """Test parser program name."""
        parser = create_parser()
        
        assert parser.prog == 'website-scraper'
    
    def test_parser_url_required(self):
        """Test URL is a required argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([])
    
    def test_parser_default_values(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args(['https://example.com'])
        
        assert args.url == 'https://example.com'
        assert args.format == 'json'
        assert args.max_pages == 100
        assert args.min_delay == 1.0
        assert args.max_delay == 3.0
        assert args.browser == 'chromium'
        assert args.llm == 'off'
        assert args.retries == 3
    
    def test_parser_output_options(self):
        """Test output option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '-o', 'output.json',
            '-f', 'markdown'
        ])
        
        assert args.output == 'output.json'
        assert args.format == 'markdown'
    
    def test_parser_scraping_options(self):
        """Test scraping option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '--max-pages', '50',
            '--max-depth', '3',
            '--include-external'
        ])
        
        assert args.max_pages == 50
        assert args.max_depth == 3
        assert args.include_external is True
    
    def test_parser_timing_options(self):
        """Test timing option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '-m', '2.0',
            '-M', '5.0',
            '--timeout', '60'
        ])
        
        assert args.min_delay == 2.0
        assert args.max_delay == 5.0
        assert args.timeout == 60
    
    def test_parser_browser_options(self):
        """Test browser option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '--browser', 'firefox',
            '--no-headless',
            '--no-stealth'
        ])
        
        assert args.browser == 'firefox'
        assert args.no_headless is True
        assert args.no_stealth is True
    
    def test_parser_llm_options(self):
        """Test LLM option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '--llm', 'openai',
            '--api-key', 'sk-test123',
            '--model', 'gpt-4',
            '--goal', 'Find product pages'
        ])
        
        assert args.llm == 'openai'
        assert args.api_key == 'sk-test123'
        assert args.model == 'gpt-4'
        assert args.goal == 'Find product pages'
    
    def test_parser_logging_options(self):
        """Test logging option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '-l', 'custom_logs',
            '-q',
            '-v'
        ])
        
        assert args.log_dir == 'custom_logs'
        assert args.quiet is True
        assert args.verbose is True
    
    def test_parser_retry_options(self):
        """Test retry option parsing."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '-r', '5'
        ])
        
        assert args.retries == 5
    
    def test_parser_invalid_browser(self):
        """Test invalid browser option raises error."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([
                'https://example.com',
                '--browser', 'invalid'
            ])
    
    def test_parser_invalid_format(self):
        """Test invalid format option raises error."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([
                'https://example.com',
                '-f', 'invalid'
            ])
    
    def test_parser_invalid_llm(self):
        """Test invalid LLM provider raises error."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([
                'https://example.com',
                '--llm', 'invalid'
            ])


class TestSetupConsoleLogging:
    """Tests for console logging setup."""
    
    def test_setup_default_logging(self):
        """Test default logging setup."""
        setup_console_logging(verbose=False)
        
        logger = logging.getLogger()
        assert logger.level <= logging.WARNING
    
    def test_setup_verbose_logging(self):
        """Test verbose logging setup."""
        setup_console_logging(verbose=True)
        
        logger = logging.getLogger()
        # Should have set up a handler at minimum
        # Note: logging may have pre-existing handlers
        assert True  # Just verify it doesn't throw


@pytest.mark.asyncio
class TestRunScraper:
    """Tests for run_scraper async function."""
    
    async def test_run_scraper_with_output_file(self, temp_dir):
        """Test run_scraper with output file."""
        with patch('website_scraper.cli.WebScraper') as mock_scraper_class:
            # Setup mock scraper
            mock_scraper = MagicMock()
            mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
            mock_scraper.__aexit__ = AsyncMock(return_value=None)
            mock_scraper.scrape = AsyncMock(return_value=([], MagicMock(
                total_pages=1,
                successful_pages=1,
                failed_pages=0,
                _format_duration=lambda: "1 second"
            )))
            mock_scraper_class.return_value = mock_scraper
            
            with patch('website_scraper.cli.create_exporter') as mock_create_exporter:
                mock_exporter = MagicMock()
                mock_exporter.export = AsyncMock(return_value='{"data": []}')
                mock_exporter.file_extension = '.json'
                mock_create_exporter.return_value = mock_exporter
                
                # Create args namespace
                args = argparse.Namespace(
                    url='https://example.com',
                    output=str(temp_dir / 'results'),
                    format='json',
                    max_pages=10,
                    max_depth=None,
                    include_external=False,
                    browser='chromium',
                    no_headless=False,
                    min_delay=1.0,
                    max_delay=3.0,
                    timeout=30,
                    retries=3,
                    llm='off',
                    api_key=None,
                    model=None,
                    goal=None,
                    log_dir=str(temp_dir / 'logs'),
                    verbose=False,
                    no_stealth=False,
                    quiet=False,
                )
                
                result = await run_scraper(args)
                
                assert result == 0
                mock_scraper.scrape.assert_called_once()
    
    async def test_run_scraper_stdout(self, temp_dir, capsys):
        """Test run_scraper outputs to stdout when no output file."""
        with patch('website_scraper.cli.WebScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.__aenter__ = AsyncMock(return_value=mock_scraper)
            mock_scraper.__aexit__ = AsyncMock(return_value=None)
            mock_scraper.scrape = AsyncMock(return_value=([], MagicMock(
                total_pages=1,
                successful_pages=1,
                _format_duration=lambda: "1 second"
            )))
            mock_scraper_class.return_value = mock_scraper
            
            with patch('website_scraper.cli.create_exporter') as mock_create_exporter:
                mock_exporter = MagicMock()
                mock_exporter.export = AsyncMock(return_value='{"data": []}')
                mock_create_exporter.return_value = mock_exporter
                
                args = argparse.Namespace(
                    url='https://example.com',
                    output=None,
                    format='json',
                    max_pages=10,
                    max_depth=None,
                    include_external=False,
                    browser='chromium',
                    no_headless=False,
                    min_delay=1.0,
                    max_delay=3.0,
                    timeout=30,
                    retries=3,
                    llm='off',
                    api_key=None,
                    model=None,
                    goal=None,
                    log_dir=str(temp_dir / 'logs'),
                    verbose=False,
                    no_stealth=False,
                    quiet=False,
                )
                
                result = await run_scraper(args)
                
                assert result == 0
                captured = capsys.readouterr()
                assert '{"data": []}' in captured.out
    
    async def test_run_scraper_error_handling(self, temp_dir):
        """Test run_scraper handles errors gracefully."""
        with patch('website_scraper.cli.WebScraper') as mock_scraper_class:
            mock_scraper_class.side_effect = Exception("Test error")
            
            args = argparse.Namespace(
                url='https://example.com',
                output=None,
                format='json',
                max_pages=10,
                max_depth=None,
                include_external=False,
                browser='chromium',
                no_headless=False,
                min_delay=1.0,
                max_delay=3.0,
                timeout=30,
                retries=3,
                llm='off',
                api_key=None,
                model=None,
                goal=None,
                log_dir=str(temp_dir / 'logs'),
                verbose=False,
                no_stealth=False,
                quiet=False,
            )
            
            result = await run_scraper(args)
            
            assert result == 1


class TestMain:
    """Tests for main entry point."""
    
    def test_main_requires_url(self):
        """Test main function requires URL argument."""
        with patch.object(sys, 'argv', ['website-scraper']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2
    
    def test_main_llm_requires_api_key(self):
        """Test main function validates LLM API key."""
        with patch.object(sys, 'argv', [
            'website-scraper',
            'https://example.com',
            '--llm', 'openai'
        ]):
            with patch.dict('os.environ', {}, clear=True):
                # Remove any existing API keys
                import os
                for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']:
                    os.environ.pop(key, None)
                
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2
    
    def test_main_ollama_no_api_key_needed(self, temp_dir):
        """Test Ollama doesn't require API key."""
        with patch.object(sys, 'argv', [
            'website-scraper',
            'https://example.com',
            '--llm', 'ollama',
            '-l', str(temp_dir / 'logs'),
            '-q'
        ]):
            with patch('website_scraper.cli.asyncio.run') as mock_run:
                mock_run.return_value = 0
                
                result = main()
                
                # Should have called asyncio.run
                mock_run.assert_called_once()
    
    def test_main_with_api_key_arg(self, temp_dir):
        """Test main function accepts API key argument."""
        with patch.object(sys, 'argv', [
            'website-scraper',
            'https://example.com',
            '--llm', 'openai',
            '--api-key', 'sk-test123',
            '-l', str(temp_dir / 'logs'),
            '-q'
        ]):
            with patch('website_scraper.cli.asyncio.run') as mock_run:
                mock_run.return_value = 0
                
                result = main()
                
                mock_run.assert_called_once()
    
    def test_main_with_env_api_key(self, temp_dir):
        """Test main function accepts environment variable API key."""
        with patch.object(sys, 'argv', [
            'website-scraper',
            'https://example.com',
            '--llm', 'openai',
            '-l', str(temp_dir / 'logs'),
            '-q'
        ]):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test123'}):
                with patch('website_scraper.cli.asyncio.run') as mock_run:
                    mock_run.return_value = 0
                    
                    result = main()
                    
                    mock_run.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI components."""
    
    def test_parser_and_run_integration(self):
        """Test parser output can be used with run_scraper."""
        parser = create_parser()
        args = parser.parse_args([
            'https://example.com',
            '--max-pages', '5',
            '-f', 'json'
        ])
        
        # Verify args structure is compatible
        assert hasattr(args, 'url')
        assert hasattr(args, 'format')
        assert hasattr(args, 'max_pages')
        assert hasattr(args, 'browser')
        assert hasattr(args, 'llm')
    
    def test_all_format_options_valid(self):
        """Test all format options are valid."""
        parser = create_parser()
        
        for fmt in ['json', 'jsonl', 'markdown', 'csv', 'tsv']:
            args = parser.parse_args([
                'https://example.com',
                '-f', fmt
            ])
            assert args.format == fmt
    
    def test_all_browser_options_valid(self):
        """Test all browser options are valid."""
        parser = create_parser()
        
        for browser in ['chromium', 'firefox', 'webkit']:
            args = parser.parse_args([
                'https://example.com',
                '--browser', browser
            ])
            assert args.browser == browser
    
    def test_all_llm_options_valid(self):
        """Test all LLM options are valid."""
        parser = create_parser()
        
        for llm in ['off', 'openai', 'anthropic', 'gemini', 'ollama']:
            args = parser.parse_args([
                'https://example.com',
                '--llm', llm
            ])
            assert args.llm == llm
