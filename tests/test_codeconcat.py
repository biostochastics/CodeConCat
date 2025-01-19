import os
import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParsedFileData,
    SecurityIssue,
    TokenStats,
)
from codeconcat.collector.local_collector import collect_local_files, should_include_file
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.parser.language_parsers.python_parser import parse_python
from codeconcat.processor.security_processor import SecurityProcessor
from codeconcat.transformer.annotator import annotate
from codeconcat.writer.markdown_writer import write_markdown


# Fixtures
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def sample_python_file(temp_dir):
    content = """
def hello_world():
    '''Say hello to the world'''
    return "Hello, World!"

class TestClass:
    def test_method(self):
        pass

CONSTANT = 42
"""
    file_path = os.path.join(temp_dir, "test.py")
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


@pytest.fixture
def sample_config():
    return CodeConCatConfig(
        target_path=".",
        extract_docs=True,
        merge_docs=False,
        format="markdown",
        output="test_output.md",
    )


# Unit Tests: Parser Tests
def test_python_parser():
    content = """
def hello():
    return "Hello"

class TestClass:
    def method(self):
        pass
"""
    parsed = parse_python("test.py", content)

    assert len(parsed.declarations) == 3
    assert any(d.name == "hello" and d.kind == "function" for d in parsed.declarations)
    assert any(d.name == "TestClass" and d.kind == "class" for d in parsed.declarations)
    assert any(d.name == "method" and d.kind == "function" for d in parsed.declarations)


def test_python_parser_edge_cases():
    content = """
# Empty file with comments
"""
    parsed = parse_python("empty.py", content)
    assert len(parsed.declarations) == 0

    content = """
def func():  # Function with no body
    pass

@decorator
def decorated_func():  # Function with decorator
    pass
"""
    parsed = parse_python("decorated.py", content)
    assert len(parsed.declarations) == 2


# Unit Tests: Security Processor Tests
def test_security_processor():
    content = """
API_KEY = "super_secret_key_12345"
password = "password123"
"""
    issues = SecurityProcessor.scan_content(content, "test.py")
    assert len(issues) > 0
    assert any("API Key" in issue.issue_type for issue in issues)


def test_security_processor_false_positives():
    content = """
EXAMPLE_KEY = "example_key"  # Should not trigger
TEST_PASSWORD = "dummy_password"  # Should not trigger
"""
    issues = SecurityProcessor.scan_content(content, "test.py")
    assert len(issues) == 0


# Integration Tests
def test_end_to_end_workflow(temp_dir, sample_python_file, sample_config):
    # Test file collection
    files = collect_local_files(temp_dir, sample_config)
    assert len(files) > 0
    assert any(f.file_path == sample_python_file for f in files)

    # Test parsing
    parsed_files = parse_code_files([f.file_path for f in files], sample_config)
    assert len(parsed_files) > 0
    first_file = parsed_files[0]
    assert isinstance(first_file, ParsedFileData)
    assert len(first_file.declarations) > 0

    # Test annotation
    annotated = annotate(first_file, sample_config)
    assert "hello_world" in annotated.annotated_content
    assert "TestClass" in annotated.annotated_content

    # Test output generation
    output_path = os.path.join(temp_dir, "output.md")
    sample_config.output = output_path
    result = write_markdown([annotated], [], sample_config)
    assert os.path.exists(output_path)
    with open(output_path, "r") as f:
        content = f.read()
        assert "hello_world" in content
        assert "TestClass" in content


# Edge Case Tests
def test_malformed_files(temp_dir):
    # Test file with invalid encoding
    invalid_file = os.path.join(temp_dir, "invalid.py")
    with open(invalid_file, "wb") as f:
        f.write(b"\x80\x81\x82")  # Invalid UTF-8

    config = CodeConCatConfig(target_path=temp_dir)
    files = collect_local_files(temp_dir, config)
    assert len(files) == 0  # Should skip invalid file


def test_large_file_handling(temp_dir):
    # Create a large file
    large_file = os.path.join(temp_dir, "large.py")
    with open(large_file, "w") as f:
        for i in range(10000):
            f.write(f"def func_{i}(): pass\n")

    config = CodeConCatConfig(target_path=temp_dir)
    files = collect_local_files(temp_dir, config)
    parsed_files = parse_code_files([f.file_path for f in files], config)
    assert len(parsed_files) == 1
    assert len(parsed_files[0].declarations) == 10000


def test_special_characters(temp_dir):
    content = """
def func_with_unicode_☺():
    pass

class TestClass_🐍:
    def test_method_💻(self):
        pass
"""
    file_path = os.path.join(temp_dir, "unicode.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    config = CodeConCatConfig(target_path=temp_dir)
    files = collect_local_files(temp_dir, config)
    parsed_files = parse_code_files([f.file_path for f in files], config)
    assert len(parsed_files) == 1
    assert any("☺" in d.name for d in parsed_files[0].declarations)
    assert any("🐍" in d.name for d in parsed_files[0].declarations)
    assert any("💻" in d.name for d in parsed_files[0].declarations)


# Performance Tests
def test_concurrent_processing(temp_dir):
    # Create multiple files
    for i in range(10):
        with open(os.path.join(temp_dir, f"test_{i}.py"), "w") as f:
            f.write(f"def func_{i}(): pass\n" * 100)

    config = CodeConCatConfig(target_path=temp_dir, max_workers=4)
    start_time = time.time()
    files = collect_local_files(temp_dir, config)
    parsed_files = parse_code_files([f.file_path for f in files], config)
    end_time = time.time()

    assert len(parsed_files) == 10
    assert end_time - start_time < 5  # Should complete within 5 seconds


# Configuration Tests
def test_config_validation():
    # Test invalid configuration
    with pytest.raises(ValueError):
        CodeConCatConfig(target_path=".", format="invalid_format")

    # Test path exclusions
    config = CodeConCatConfig(target_path=".", exclude_paths=["*.pyc", "__pycache__"])
    assert not should_include_file("test.pyc", config)
    assert not should_include_file("__pycache__/test.py", config)
    assert should_include_file("test.py", config)


# Token Statistics Tests
def test_token_counting():
    content = "def test_function(): pass"
    parsed = ParsedFileData(
        file_path="test.py",
        language="python",
        content=content,
        token_stats=TokenStats(gpt3_tokens=10, gpt4_tokens=10, davinci_tokens=10, claude_tokens=8),
    )

    assert parsed.token_stats.gpt3_tokens > 0
    assert parsed.token_stats.gpt4_tokens > 0
    assert parsed.token_stats.davinci_tokens > 0
    assert parsed.token_stats.claude_tokens > 0


def test_disable_ai_context(temp_dir):
    # Create test files
    code_file = os.path.join(temp_dir, "main.py")
    with open(code_file, "w") as f:
        f.write(
            """
def main():
    print("Hello, World!")
"""
        )

    config = CodeConCatConfig(target_path=temp_dir)
    files = collect_local_files(temp_dir, config)
    parsed_files = parse_code_files([f.file_path for f in files], config)
    assert len(parsed_files) == 1
    assert len(parsed_files[0].declarations) == 1


def test_merge_docs(temp_dir):
    # Create test files
    code_file = os.path.join(temp_dir, "main.py")
    with open(code_file, "w") as f:
        f.write(
            """
def main():
    \"\"\"Main function.\"\"\"
    print("Hello, World!")
"""
        )

    config = CodeConCatConfig(target_path=temp_dir)
    files = collect_local_files(temp_dir, config)
    parsed_files = parse_code_files([f.file_path for f in files], config)
    assert len(parsed_files) == 1
    assert len(parsed_files[0].declarations) == 1
    assert parsed_files[0].declarations[0].docstring == "Main function."


if __name__ == "__main__":
    # Run tests with coverage when executing the file directly
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "--cov=codeconcat", __file__]))
