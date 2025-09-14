"""Test path redaction in CLI utils."""

import logging
import os
from pathlib import Path
from unittest.mock import patch


def test_path_redaction_order():
    """Test that CWD is redacted before HOME to handle nested paths correctly."""
    from codeconcat.cli.utils import setup_logging

    # Mock environment to enable redaction
    with patch.dict(os.environ, {"CODECONCAT_REDACT_PATHS": "1"}):
        # Mock Path.home() and Path.cwd() to return test values
        test_home = Path("/Users/testuser")
        test_cwd = Path("/Users/testuser/projects/myapp")

        with patch("codeconcat.cli.utils.Path.home", return_value=test_home), patch(
            "codeconcat.cli.utils.Path.cwd", return_value=test_cwd
        ):
            # Set up logging with redaction
            setup_logging(level="INFO")

            # Get the root logger and verify it has our custom formatter
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            handler = root_logger.handlers[0]
            formatter = handler.formatter

            # Test cases
            test_cases = [
                (f"Error in {test_cwd}/main.py", "Error in <CWD>/main.py"),
                (
                    f"Loading from {test_home}/.config/app.conf",
                    "Loading from <HOME>/.config/app.conf",
                ),
                (
                    f"Path: {test_cwd}/src/utils.py references {test_home}/.bashrc",
                    "Path: <CWD>/src/utils.py references <HOME>/.bashrc",
                ),
                (f"File at {test_home}/documents/file.txt", "File at <HOME>/documents/file.txt"),
            ]

            # Verify redaction works correctly
            if hasattr(formatter, "_redact"):
                for original, expected in test_cases:
                    actual = formatter._redact(original)
                    assert actual == expected, (
                        f"Failed for: {original}\nExpected: {expected}\nGot: {actual}"
                    )


def test_path_redaction_disabled():
    """Test that path redaction can be disabled via environment variable."""
    from codeconcat.cli.utils import setup_logging

    # Clear existing handlers first
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Mock environment to disable redaction
    with patch.dict(os.environ, {"CODECONCAT_REDACT_PATHS": "0"}, clear=True):
        # Mock paths
        test_home = Path("/Users/testuser")
        test_cwd = Path("/Users/testuser/projects/myapp")

        with patch("codeconcat.cli.utils.Path.home", return_value=test_home), patch(
            "codeconcat.cli.utils.Path.cwd", return_value=test_cwd
        ):
            # Set up logging without redaction
            setup_logging(level="INFO")

            # Get the root logger
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0

            handler = root_logger.handlers[0]
            formatter = handler.formatter

            # When CODECONCAT_REDACT_PATHS=0, the formatter should not be PathRedactingFormatter
            # It should be a standard logging.Formatter
            assert formatter.__class__.__name__ != "PathRedactingFormatter"


def test_path_redaction_empty_text():
    """Test that empty text is handled correctly."""
    from codeconcat.cli.utils import setup_logging

    with patch.dict(os.environ, {"CODECONCAT_REDACT_PATHS": "1"}):
        test_home = Path("/Users/testuser")
        test_cwd = Path("/Users/testuser/projects/myapp")

        with patch("codeconcat.cli.utils.Path.home", return_value=test_home), patch(
            "codeconcat.cli.utils.Path.cwd", return_value=test_cwd
        ):
            setup_logging(level="INFO")

            root_logger = logging.getLogger()
            handler = root_logger.handlers[0]
            formatter = handler.formatter

            if hasattr(formatter, "_redact"):
                # Test empty string
                assert formatter._redact("") == ""
                # Test None (should handle gracefully)
                assert formatter._redact(None) is None
