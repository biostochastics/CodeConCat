"""
Pytest configuration for API tests.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def enable_local_path_for_api_tests():
    """Enable local path access for API tests by setting test environment."""
    # Set environment to test mode to disable production security restrictions
    original_env = os.environ.get("ENV")
    os.environ["ENV"] = "test"

    yield

    # Clean up after tests
    if original_env is not None:
        os.environ["ENV"] = original_env
    elif "ENV" in os.environ:
        del os.environ["ENV"]
