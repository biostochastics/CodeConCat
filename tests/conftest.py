import pytest

@pytest.fixture
def sample_code():
    return """
def hello_world():
    return "Hello, World!"
"""
