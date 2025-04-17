"""Tests for the content processor module."""

import pytest

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParsedFileData,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
)
from codeconcat.processor.content_processor import (
    generate_directory_structure,
    generate_file_summary,
    process_file_content,
)


def test_process_file_content_basic():
    content = "line1\nline2\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=False, remove_comments=False, show_line_numbers=False
    )
    result = process_file_content(content, config)
    assert result == content


def test_process_file_content_with_line_numbers():
    content = "line1\nline2\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=False, remove_comments=False, show_line_numbers=True
    )
    result = process_file_content(content, config)
    expected = "   1 | line1\n   2 | line2\n   3 | line3"
    assert result == expected


def test_process_file_content_remove_empty_lines():
    content = "line1\n\nline2\n\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=True, remove_comments=False, show_line_numbers=False
    )
    result = process_file_content(content, config)
    assert result == "line1\nline2\nline3"


def test_process_file_content_remove_comments():
    content = "line1\n# comment\nline2\n// comment\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=False, remove_comments=True, show_line_numbers=False
    )
    result = process_file_content(content, config)
    assert result == "line1\nline2\nline3"


def test_generate_file_summary():
    file_data = ParsedFileData(
        file_path="/path/to/test.py",
        language="python",
        content="test content",
        declarations=[
            Declaration(
                kind="function",
                name="test_func",
                start_line=1,
                end_line=5,
                modifiers=set(),
                docstring=None,
            )
        ],
        token_stats=TokenStats(input_tokens=100, output_tokens=120, total_tokens=220),
        security_issues=[
            SecurityIssue(
                rule_id="hardcoded_secret",
                description="Hardcoded password found in source code",
                file_path="/path/to/test.py",
                line_number=3,
                severity=SecuritySeverity.HIGH,
                context="password = 'secret'",
            )
        ],
    )

    summary = generate_file_summary(file_data)
    assert "test.py" in summary
    assert "python" in summary
    assert "  - Total: 220" in summary
    assert "hardcoded_secret" in summary
    assert "function: test_func" in summary


def test_generate_directory_structure():
    file_paths = ["src/main.py", "src/utils/helper.py", "tests/test_main.py"]
    structure = generate_directory_structure(file_paths)
    assert "src" in structure
    assert "main.py" in structure
    assert "utils" in structure
    assert "helper.py" in structure
    assert "tests" in structure
    assert "test_main.py" in structure
