"""Tests for the content processor module."""

import pytest
from codeconcat.base_types import (
    CodeConCatConfig,
    ParsedFileData,
    TokenStats,
    SecurityIssue,
    Declaration
)
from codeconcat.processor.content_processor import (
    process_file_content,
    generate_file_summary,
    generate_directory_structure
)


def test_process_file_content_basic():
    content = "line1\nline2\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=False,
        remove_comments=False,
        show_line_numbers=False
    )
    result = process_file_content(content, config)
    assert result == content


def test_process_file_content_with_line_numbers():
    content = "line1\nline2\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=False,
        remove_comments=False,
        show_line_numbers=True
    )
    result = process_file_content(content, config)
    expected = "   1 | line1\n   2 | line2\n   3 | line3"
    assert result == expected


def test_process_file_content_remove_empty_lines():
    content = "line1\n\nline2\n\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=True,
        remove_comments=False,
        show_line_numbers=False
    )
    result = process_file_content(content, config)
    assert result == "line1\nline2\nline3"


def test_process_file_content_remove_comments():
    content = "line1\n# comment\nline2\n// comment\nline3"
    config = CodeConCatConfig(
        remove_empty_lines=False,
        remove_comments=True,
        show_line_numbers=False
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
                docstring=None
            )
        ],
        token_stats=TokenStats(
            gpt3_tokens=100,
            gpt4_tokens=120,
            davinci_tokens=110,
            claude_tokens=115
        ),
        security_issues=[
            SecurityIssue(
                issue_type="hardcoded_secret",
                line_number=3,
                line_content="password = 'secret'",
                severity="high",
                description="Hardcoded password found in source code"
            )
        ]
    )
    
    summary = generate_file_summary(file_data)
    assert "test.py" in summary
    assert "python" in summary
    assert "GPT-3.5: 100" in summary
    assert "hardcoded_secret" in summary
    assert "function: test_func" in summary


def test_generate_directory_structure():
    file_paths = [
        "src/main.py",
        "src/utils/helper.py",
        "tests/test_main.py"
    ]
    structure = generate_directory_structure(file_paths)
    assert "src" in structure
    assert "main.py" in structure
    assert "utils" in structure
    assert "helper.py" in structure
    assert "tests" in structure
    assert "test_main.py" in structure
