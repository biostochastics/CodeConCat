"""Comprehensive tests for CLI utility functions."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import typer
from rich.console import Console
from rich.table import Table

from codeconcat.cli.utils import (
    confirm_action,
    console,
    create_progress_spinner,
    format_file_size,
    get_language_color,
    print_error,
    print_file_stats,
    print_info,
    print_success,
    print_warning,
    setup_logging,
    show_quote,
    validate_path,
)


class TestCLIUtils:
    """Test suite for CLI utility functions."""

    def test_console_instance(self):
        """Test that console is a Console instance."""
        assert isinstance(console, Console)

    @patch("codeconcat.cli.utils.logging.basicConfig")
    @patch.dict("os.environ", {}, clear=True)
    def test_setup_logging_default(self, mock_basic_config):
        """Test logging setup with default settings."""
        setup_logging()

        mock_basic_config.assert_called_once()
        # Check environment variable is set
        import os

        assert os.environ.get("TOKENIZERS_PARALLELISM") == "false"

    @patch("codeconcat.cli.utils.logging.basicConfig")
    @patch("codeconcat.cli.utils.logging.getLogger")
    def test_setup_logging_debug(self, mock_get_logger, mock_basic_config):
        """Test logging setup with DEBUG level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        setup_logging(level="DEBUG")

        mock_basic_config.assert_called_once()
        # In debug mode, library loggers should not be suppressed

    @patch("codeconcat.cli.utils.logging.basicConfig")
    @patch("codeconcat.cli.utils.logging.getLogger")
    def test_setup_logging_info(self, mock_get_logger, _mock_basic_config):
        """Test logging setup with INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        setup_logging(level="INFO")

        # Library loggers should be set to WARNING
        assert mock_get_logger.call_count >= 1

    @patch("codeconcat.cli.utils.get_random_quote")
    @patch("codeconcat.cli.utils.console")
    def test_show_quote_normal(self, mock_console, mock_get_quote):
        """Test showing a normal quote."""
        mock_get_quote.return_value = "Test quote"

        show_quote(quiet=False)

        mock_get_quote.assert_called_once()
        mock_console.print.assert_called()

    @patch("codeconcat.cli.utils.get_random_quote")
    @patch("codeconcat.cli.utils.console")
    def test_show_quote_cat(self, mock_console, mock_get_quote):
        """Test showing a cat-related quote."""
        mock_get_quote.return_value = "Cats are awesome!"

        show_quote(quiet=False)

        mock_console.print.assert_called()
        # Cat quotes should be cyan - check the Panel object
        args = mock_console.print.call_args_list[0][0][0]
        assert hasattr(args, "renderable")  # Should be a Panel
        assert hasattr(args.renderable, "style")  # Should have Text with style
        assert args.renderable.style == "cyan italic"

    @patch("codeconcat.cli.utils.get_random_quote")
    @patch("codeconcat.cli.utils.console")
    def test_show_quote_quiet(self, _mock_console, mock_get_quote):
        """Test quiet mode suppresses quotes."""
        show_quote(quiet=True)

        mock_get_quote.assert_not_called()

    @patch("codeconcat.cli.utils.Progress")
    def test_create_progress_spinner(self, mock_progress_class):
        """Test progress spinner creation."""
        mock_progress = MagicMock()
        mock_progress_class.return_value = mock_progress

        result = create_progress_spinner("Testing...")

        assert result == mock_progress
        mock_progress_class.assert_called_once()

    @patch("codeconcat.cli.utils.console")
    def test_print_file_stats(self, mock_console):
        """Test file statistics printing."""
        stats = {"total_files": 100, "total_lines": 5000, "file_size": "1.2 MB"}

        print_file_stats(stats)

        # Should create and print a table
        mock_console.print.assert_called_once()
        table_arg = mock_console.print.call_args[0][0]
        assert isinstance(table_arg, Table)

    def test_validate_path_exists(self):
        """Test path validation for existing path."""
        # Use a path that definitely exists
        test_path = Path(__file__)  # This test file itself

        result = validate_path(test_path, must_exist=True)
        assert result.exists()

    @patch("codeconcat.cli.utils.console")
    def test_validate_path_not_exists(self, mock_console):
        """Test path validation for non-existing path."""
        test_path = Path("/definitely/does/not/exist/path.txt")

        with pytest.raises(typer.Exit):
            validate_path(test_path, must_exist=True)

        mock_console.print.assert_called_once()

    def test_validate_path_no_check(self):
        """Test path validation without existence check."""
        test_path = Path("/any/path")

        result = validate_path(test_path, must_exist=False)
        assert isinstance(result, Path)

    @patch("typer.confirm")
    def test_confirm_action_yes(self, mock_confirm):
        """Test user confirmation with yes."""
        mock_confirm.return_value = True

        result = confirm_action("Continue?")

        assert result is True
        mock_confirm.assert_called_once_with("Continue?", default=False)

    @patch("typer.confirm")
    def test_confirm_action_no(self, mock_confirm):
        """Test user confirmation with no."""
        mock_confirm.return_value = False

        result = confirm_action("Continue?", default=True)

        assert result is False
        mock_confirm.assert_called_once_with("Continue?", default=True)

    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        assert format_file_size(0) == "0.0 B"
        assert format_file_size(100) == "100.0 B"
        assert format_file_size(1023) == "1023.0 B"

    def test_format_file_size_kb(self):
        """Test file size formatting for kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(10240) == "10.0 KB"

    def test_format_file_size_mb(self):
        """Test file size formatting for megabytes."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 5.5) == "5.5 MB"

    def test_format_file_size_gb(self):
        """Test file size formatting for gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1024 * 1024 * 1024 * 2.7) == "2.7 GB"

    def test_get_language_color(self):
        """Test language color mapping."""
        assert get_language_color("python") == "yellow"
        assert get_language_color("javascript") == "cyan"
        assert get_language_color("rust") == "orange1"
        assert get_language_color("unknown") == "white"  # Default
        assert get_language_color("PYTHON") == "yellow"  # Case insensitive

    @patch("codeconcat.cli.utils.console")
    def test_print_error_with_exit(self, mock_console):
        """Test error printing with exit."""
        with pytest.raises(typer.Exit) as exc_info:
            print_error("Test error", exit_code=1)

        assert exc_info.value.exit_code == 1
        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "[bold red]Error:[/bold red]" in args
        assert "Test error" in args

    @patch("codeconcat.cli.utils.console")
    def test_print_error_with_custom_exit(self, _mock_console):
        """Test error printing with custom exit code."""
        with pytest.raises(typer.Exit) as exc_info:
            print_error("Critical error", exit_code=2)

        assert exc_info.value.exit_code == 2

    @patch("codeconcat.cli.utils.console")
    def test_print_success(self, mock_console):
        """Test success message printing."""
        print_success("Operation completed")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "[bold green]✓[/bold green]" in args
        assert "Operation completed" in args

    @patch("codeconcat.cli.utils.console")
    def test_print_warning(self, mock_console):
        """Test warning message printing."""
        print_warning("This is a warning")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "[bold yellow]⚠[/bold yellow]" in args
        assert "This is a warning" in args

    @patch("codeconcat.cli.utils.console")
    def test_print_info(self, mock_console):
        """Test info message printing."""
        print_info("Information message")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "[bold blue]ℹ[/bold blue]" in args
        assert "Information message" in args

    def test_format_file_size_edge_cases(self):
        """Test edge cases for file size formatting."""
        # Test TB
        assert "TB" in format_file_size(1024 * 1024 * 1024 * 1024)
        # Test PB (very large)
        assert "PB" in format_file_size(1024 * 1024 * 1024 * 1024 * 1024)

    @patch("codeconcat.cli.utils.console")
    def test_print_file_stats_empty(self, mock_console):
        """Test printing empty stats."""
        print_file_stats({})

        mock_console.print.assert_called_once()
        # Should still create a table even if empty

    def test_get_language_color_variations(self):
        """Test language color for various languages."""
        languages = {
            "java": "red",
            "cpp": "magenta",
            "c": "magenta",
            "go": "cyan",
            "ruby": "red",
            "php": "purple",
            "csharp": "green",
            "swift": "orange1",
            "kotlin": "purple",
            "r": "blue",
            "julia": "purple",
            "typescript": "blue",
        }

        for lang, color in languages.items():
            assert get_language_color(lang) == color
