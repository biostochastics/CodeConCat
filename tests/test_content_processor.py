import pytest
from freezegun import freeze_time
from codeconcat.base_types import (
    CodeConCatConfig,
    ParsedFileData,
    SecurityIssue,
    TokenStats,
    Declaration
)
from codeconcat.processor.content_processor import (
    process_file_content,
    generate_file_summary,
    generate_directory_structure
)

@pytest.fixture
def basic_config():
    return CodeConCatConfig(
        target_path="dummy_path",
        github_url=None,
        github_token=None,
        github_ref=None,
        include_languages=[],
        exclude_languages=[],
        include_paths=[],
        exclude_paths=[],
        extract_docs=True,
        merge_docs=True,
        output="output.md",
        format="markdown",
        max_workers=4,
        disable_tree=False,
        disable_copy=False,
        disable_annotations=False,
        disable_symbols=False,
        disable_ai_context=False
    )

@pytest.fixture
def complex_file_data():
    return ParsedFileData(
        file_path="/path/to/test.py",
        content="def test():\n    pass",
        language="python",
        token_stats=TokenStats(
            gpt3_tokens=10,
            gpt4_tokens=12,
            davinci_tokens=11,
            claude_tokens=13
        ),
        security_issues=[
            SecurityIssue(
                issue_type="hardcoded_secret",
                line_number=5,
                line_content="api_key = 'secret123'",
                severity="HIGH",
                description="Hardcoded API key found in code"
            ),
            SecurityIssue(
                issue_type="sql_injection",
                line_number=10,
                line_content="query = f'SELECT * FROM users WHERE id = {user_input}'",
                severity="CRITICAL",
                description="Potential SQL injection vulnerability"
            )
        ],
        declarations=[
            Declaration(
                kind="class",
                name="TestClass",
                start_line=1,
                end_line=20
            ),
            Declaration(
                kind="function",
                name="test_method",
                start_line=5,
                end_line=10
            )
        ]
    )

def test_process_file_content_comprehensive(basic_config):
    """Test file content processing with various configurations."""
    content = '''# Comment line
def test():
    # Nested comment
    print("Hello")  # Inline comment

    return True'''

    # Test with default config (no special processing)
    result = process_file_content(content, basic_config)
    assert "# Comment line" in result
    assert "# Nested comment" in result
    assert "# Inline comment" in result

    # Test with comments removed
    config = basic_config
    config.disable_annotations = True
    result = process_file_content(content, config)
    assert "# Comment line" not in result
    assert "# Nested comment" not in result
    assert "# Inline comment" not in result
    assert "def test():" in result

    # Test with empty lines removed
    config = basic_config
    config.remove_empty_lines = True
    result = process_file_content(content, config)
    assert not any(line.strip() == "" for line in result.split("\n"))

def test_process_file_content_edge_cases(basic_config):
    """Test file content processing with edge cases."""
    # Test empty content
    assert process_file_content("", basic_config) == ""

    # Test single line
    content = "single line"
    assert process_file_content(content, basic_config) == content

    # Test multiple empty lines
    content = "\n\n\n"
    config = basic_config
    config.remove_empty_lines = True
    assert process_file_content(content, config) == ""

    # Test mixed comment styles
    content = '''# Python comment
// JavaScript comment
/* C-style comment */
''' + '""" Docstring """'
    config = basic_config
    config.disable_annotations = True
    result = process_file_content(content, config)
    assert "# Python comment" not in result
    assert "// JavaScript comment" not in result
    assert "/* C-style comment */" not in result
    assert '""" Docstring """' not in result

def test_generate_file_summary_comprehensive(complex_file_data):
    """Test file summary generation with various data."""
    summary = generate_file_summary(complex_file_data)
    
    # Check basic file info
    assert "File: test.py" in summary
    assert "Language: python" in summary
    
    # Check token stats
    assert "Token Counts:" in summary
    assert "GPT-3.5: 10" in summary
    assert "GPT-4: 12" in summary
    assert "Davinci: 11" in summary
    assert "Claude: 13" in summary
    
    # Check security issues
    assert "Security Issues:" in summary
    assert "hardcoded_secret" in summary
    assert "sql_injection" in summary
    assert "Line 5" in summary
    assert "Line 10" in summary
    assert "HIGH" in summary
    assert "CRITICAL" in summary
    
    # Check declarations
    assert "Declarations:" in summary
    assert "class: TestClass" in summary
    assert "function: test_method" in summary
    assert "lines 1-20" in summary
    assert "lines 5-10" in summary

def test_generate_file_summary_edge_cases():
    """Test file summary generation with edge cases."""
    # Test minimal file data
    minimal_data = ParsedFileData(
        file_path="test.py",
        content="",
        language="python"
    )
    summary = generate_file_summary(minimal_data)
    assert "File: test.py" in summary
    assert "Language: python" in summary
    assert "Token Counts:" not in summary
    assert "Security Issues:" not in summary
    assert "Declarations:" not in summary

def test_generate_directory_structure():
    """Test directory structure generation with various paths."""
    # Test simple structure
    paths = [
        "src/main.py",
        "src/utils.py",
        "tests/test_main.py"
    ]
    structure = generate_directory_structure(paths)
    assert "src" in structure
    assert "main.py" in structure
    assert "tests" in structure
    
    # Test nested structure
    paths = [
        "src/main.py",
        "src/utils/helper.py",
        "src/utils/config/settings.py",
        "tests/unit/test_main.py",
        "tests/integration/test_api.py"
    ]
    structure = generate_directory_structure(paths)
    assert "src" in structure
    assert "utils" in structure
    assert "config" in structure
    assert "unit" in structure
    assert "integration" in structure
    
    # Test empty input
    assert generate_directory_structure([]) == ""
    
    # Test single file
    structure = generate_directory_structure(["file.txt"])
    assert "file.txt" in structure
    assert "└── " in structure  # Should use tree structure characters
