#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pytest configuration file for CodeConCat tests.

This file contains shared fixtures and configuration for all unit and integration tests.
"""

import os
import logging
import pytest
import sys

# Add the project root to the Python path for reliable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now we can safely import from the codeconcat package
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging  # noqa: E402

# Enable debug logging for all parsers by default for test runs
enable_all_parser_debug_logging()

# Configure root logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Ensure the test environment is properly set up
def pytest_configure(config):
    """Set up the pytest environment."""
    logger.info("Setting up CodeConCat test environment")

    # Make sure the package is importable
    import codeconcat

    logger.info(f"Testing CodeConCat version located at: {codeconcat.__file__}")

    # Log pytest configuration
    logger.info(f"Running with pytest config: {config.option}")


# Define common fixtures that can be used across test files
@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    # The project root is 2 levels up from this file
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def test_corpus_dir(project_root):
    """Return the path to the test corpus directory."""
    return os.path.join(project_root, "tests", "parser_test_corpus")
