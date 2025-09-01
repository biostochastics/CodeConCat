"""Comprehensive tests for the API CLI module."""

import logging
from unittest.mock import patch

from codeconcat.api.cli import build_parser, cli_entry_point


class TestBuildParser:
    """Test the argument parser builder."""

    def test_build_parser_creates_parser(self):
        """Test that build_parser creates a valid ArgumentParser."""
        parser = build_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parser_has_all_arguments(self):
        """Test that all expected arguments are present."""
        parser = build_parser()

        # Parse with defaults
        args = parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 8000
        assert args.log_level == "info"
        assert args.reload is False
        assert args.version is False

    def test_parser_custom_host_port(self):
        """Test parsing custom host and port."""
        parser = build_parser()
        args = parser.parse_args(["--host", "0.0.0.0", "--port", "9000"])
        assert args.host == "0.0.0.0"
        assert args.port == 9000

    def test_parser_log_levels(self):
        """Test all valid log levels."""
        parser = build_parser()
        for level in ["debug", "info", "warning", "error", "critical"]:
            args = parser.parse_args(["--log-level", level])
            assert args.log_level == level

    def test_parser_reload_flag(self):
        """Test reload flag."""
        parser = build_parser()
        args = parser.parse_args(["--reload"])
        assert args.reload is True

    def test_parser_version_flag(self):
        """Test version flag."""
        parser = build_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True


class TestCliEntryPoint:
    """Test the CLI entry point function."""

    @patch("codeconcat.api.cli.start_server")
    @patch("sys.argv", ["api", "--host", "0.0.0.0", "--port", "8080"])
    def test_cli_entry_point_starts_server(self, mock_start_server):
        """Test that CLI entry point starts the server with correct args."""
        with patch("codeconcat.api.cli.version.__version__", "1.0.0"):
            result = cli_entry_point()

        assert result == 0
        mock_start_server.assert_called_once_with(
            host="0.0.0.0", port=8080, log_level="info", reload=False
        )

    @patch("builtins.print")
    @patch("sys.argv", ["api", "--version"])
    def test_cli_entry_point_version(self, mock_print):
        """Test version display."""
        with patch("codeconcat.api.cli.version.__version__", "1.2.3"):
            result = cli_entry_point()

        assert result == 0
        mock_print.assert_called_once_with("CodeConCat API v1.2.3")

    @patch("builtins.print")
    @patch("sys.argv", ["api", "--version"])
    def test_cli_entry_point_version_fallback(self, mock_print):
        """Test version display with missing version attribute."""
        with patch("codeconcat.api.cli.version") as mock_version:
            del mock_version.__version__
            result = cli_entry_point()

        assert result == 0
        mock_print.assert_called_once_with("CodeConCat API vunknown")

    @patch("codeconcat.api.cli.start_server")
    @patch("sys.argv", ["api", "--log-level", "debug"])
    def test_cli_entry_point_log_level(self, _mock_start_server):
        """Test that log level is properly configured."""
        with patch("codeconcat.api.cli.logging.basicConfig") as mock_config, patch(
            "codeconcat.api.cli.version.__version__", "1.0.0"
        ):
            result = cli_entry_point()

        assert result == 0
        mock_config.assert_called_once()
        call_kwargs = mock_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    @patch("codeconcat.api.cli.start_server")
    @patch("sys.argv", ["api"])
    def test_cli_entry_point_server_error(self, mock_start_server):
        """Test error handling when server fails to start."""
        mock_start_server.side_effect = Exception("Server error")

        with patch("codeconcat.api.cli.logger") as mock_logger:
            result = cli_entry_point()

        assert result == 1
        mock_logger.error.assert_called_once()
        assert "Failed to start API server" in str(mock_logger.error.call_args)

    @patch("codeconcat.api.cli.start_server")
    @patch("sys.argv", ["api", "--reload"])
    def test_cli_entry_point_with_reload(self, mock_start_server):
        """Test CLI with reload flag."""
        with patch("codeconcat.api.cli.version.__version__", "1.0.0"):
            result = cli_entry_point()

        assert result == 0
        mock_start_server.assert_called_once()
        assert mock_start_server.call_args[1]["reload"] is True

    @patch("codeconcat.api.cli.start_server")
    @patch("sys.argv", ["api", "--host", "localhost", "--port", "3000", "--log-level", "warning"])
    def test_cli_entry_point_all_options(self, mock_start_server):
        """Test CLI with all options specified."""
        with patch("codeconcat.api.cli.version.__version__", "1.0.0"), patch(
            "codeconcat.api.cli.logging.basicConfig"
        ) as mock_config:
            result = cli_entry_point()

        assert result == 0
        mock_start_server.assert_called_once_with(
            host="localhost", port=3000, log_level="warning", reload=False
        )

        # Check logging was configured
        mock_config.assert_called_once()
        assert mock_config.call_args[1]["level"] == logging.WARNING

    @patch("codeconcat.api.cli.start_server")
    @patch("codeconcat.api.cli.logger")
    @patch("sys.argv", ["api"])
    def test_cli_entry_point_logs_startup(self, mock_logger, _mock_start_server):
        """Test that startup is properly logged."""
        with patch("codeconcat.api.cli.version.__version__", "2.0.0"):
            result = cli_entry_point()

        assert result == 0

        # Check info logs
        info_calls = mock_logger.info.call_args_list
        assert len(info_calls) == 2
        assert "Starting CodeConCat API server v2.0.0" in str(info_calls[0])
        assert "Binding to 127.0.0.1:8000" in str(info_calls[1])
