"""
Unit tests for the CodeConCat API CLI module.
"""

import pytest
import argparse
from unittest.mock import patch, MagicMock
import logging

from codeconcat.api.cli import build_parser, cli_entry_point
from codeconcat import version


class TestBuildParser:
    """Test suite for the build_parser function."""

    def test_build_parser_creates_argument_parser(self):
        """Test that build_parser returns an ArgumentParser instance."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_has_all_arguments(self):
        """Test that the parser has all expected arguments."""
        parser = build_parser()

        # Get all argument names
        actions = parser._actions
        arg_names = [action.dest for action in actions if action.dest != "help"]

        expected_args = ["host", "port", "log_level", "reload", "version"]
        for arg in expected_args:
            assert arg in arg_names

    def test_parser_default_values(self):
        """Test that parser has correct default values."""
        parser = build_parser()
        args = parser.parse_args([])

        assert args.host == "127.0.0.1"
        assert args.port == 8000
        assert args.log_level == "info"
        assert args.reload is False
        assert args.version is False

    def test_parser_custom_values(self):
        """Test parsing custom argument values."""
        parser = build_parser()
        args = parser.parse_args(
            ["--host", "0.0.0.0", "--port", "9000", "--log-level", "debug", "--reload"]
        )

        assert args.host == "0.0.0.0"
        assert args.port == 9000
        assert args.log_level == "debug"
        assert args.reload is True

    def test_parser_version_flag(self):
        """Test parsing version flag."""
        parser = build_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True

    def test_parser_invalid_log_level(self):
        """Test that invalid log level raises error."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--log-level", "invalid"])


class TestCliEntryPoint:
    """Test suite for the cli_entry_point function."""

    @patch("codeconcat.api.cli.build_parser")
    def test_cli_version_flag(self, mock_build_parser, capsys):
        """Test CLI with --version flag."""
        mock_args = MagicMock()
        mock_args.version = True

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = cli_entry_point()

        assert result == 0
        captured = capsys.readouterr()
        assert f"CodeConCat API v{version.__version__}" in captured.out

    @patch("codeconcat.api.cli.start_server")
    @patch("codeconcat.api.cli.build_parser")
    @patch("logging.basicConfig")
    def test_cli_start_server_success(self, mock_logging, mock_build_parser, mock_start_server):
        """Test successful server start."""
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.host = "127.0.0.1"
        mock_args.port = 8000
        mock_args.log_level = "info"
        mock_args.reload = False

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = cli_entry_point()

        assert result == 0
        mock_start_server.assert_called_once_with(
            host="127.0.0.1", port=8000, log_level="info", reload=False
        )

        # Check logging was configured
        mock_logging.assert_called_once()
        call_kwargs = mock_logging.call_args[1]
        assert call_kwargs["level"] == logging.INFO

    @patch("codeconcat.api.cli.start_server")
    @patch("codeconcat.api.cli.build_parser")
    @patch("logging.basicConfig")
    def test_cli_start_server_with_custom_args(
        self, mock_logging, mock_build_parser, mock_start_server
    ):
        """Test server start with custom arguments."""
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.host = "0.0.0.0"
        mock_args.port = 9000
        mock_args.log_level = "debug"
        mock_args.reload = True

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = cli_entry_point()

        assert result == 0
        mock_start_server.assert_called_once_with(
            host="0.0.0.0", port=9000, log_level="debug", reload=True
        )

        # Check logging was configured with debug level
        mock_logging.assert_called_once()
        call_kwargs = mock_logging.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    @patch("codeconcat.api.cli.start_server")
    @patch("codeconcat.api.cli.build_parser")
    @patch("codeconcat.api.cli.logger")
    def test_cli_start_server_failure(self, mock_logger, mock_build_parser, mock_start_server):
        """Test server start failure handling."""
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.host = "127.0.0.1"
        mock_args.port = 8000
        mock_args.log_level = "info"
        mock_args.reload = False

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        # Simulate server start failure
        mock_start_server.side_effect = Exception("Server failed to start")

        result = cli_entry_point()

        assert result == 1
        mock_logger.error.assert_called_with("Failed to start API server: Server failed to start")

    @patch("codeconcat.api.cli.build_parser")
    @patch("logging.basicConfig")
    def test_cli_logging_levels(self, mock_logging, mock_build_parser):
        """Test that all logging levels are correctly configured."""
        log_levels = ["debug", "info", "warning", "error", "critical"]

        for level in log_levels:
            mock_args = MagicMock()
            mock_args.version = False
            mock_args.host = "127.0.0.1"
            mock_args.port = 8000
            mock_args.log_level = level
            mock_args.reload = False

            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = mock_args
            mock_build_parser.return_value = mock_parser

            with patch("codeconcat.api.cli.start_server"):
                cli_entry_point()

            # Check logging was configured with correct level
            call_kwargs = mock_logging.call_args[1]
            expected_level = getattr(logging, level.upper())
            assert call_kwargs["level"] == expected_level
