"""Tests for the annotator module."""

from codeconcat.base_types import CodeConCatConfig, Declaration, ParsedFileData
from codeconcat.transformer.annotator import annotate


def test_annotate_empty_file():
    parsed_data = ParsedFileData(
        file_path="/path/to/empty.py", language="python", content="", declarations=[]
    )
    config = CodeConCatConfig()

    result = annotate(parsed_data, config)
    assert result.summary == "No declarations found"
    assert result.tags == ["python"]
    assert "## File: /path/to/empty.py" in result.annotated_content


def test_annotate_with_declarations():
    parsed_data = ParsedFileData(
        file_path="/path/to/test.py",
        language="python",
        content="def test(): pass\nclass Test: pass",
        declarations=[
            Declaration(
                kind="function",
                name="test",
                start_line=1,
                end_line=1,
                modifiers=set(),
                docstring=None,
            ),
            Declaration(
                kind="class",
                name="Test",
                start_line=2,
                end_line=2,
                modifiers=set(),
                docstring=None,
            ),
        ],
    )
    config = CodeConCatConfig()

    result = annotate(parsed_data, config)
    assert "1 functions, 1 classes" in result.summary
    assert set(result.tags) == {"has_functions", "has_classes", "python"}
    assert "### Functions" in result.annotated_content
    assert "### Classes" in result.annotated_content
    assert "- test" in result.annotated_content
    assert "- Test" in result.annotated_content


def test_annotate_with_structs():
    parsed_data = ParsedFileData(
        file_path="/path/to/test.cpp",
        language="cpp",
        content="struct Test { int x; };",
        declarations=[
            Declaration(
                kind="struct",
                name="Test",
                start_line=1,
                end_line=1,
                modifiers=set(),
                docstring=None,
            )
        ],
    )
    config = CodeConCatConfig()

    result = annotate(parsed_data, config)
    assert "1 structs" in result.summary
    assert set(result.tags) == {"has_structs", "cpp"}
    assert "### Structs" in result.annotated_content
    assert "- Test" in result.annotated_content


def test_annotate_with_symbols():
    parsed_data = ParsedFileData(
        file_path="/path/to/test.py",
        language="python",
        content="x = 1",
        declarations=[
            Declaration(
                kind="symbol",
                name="x",
                start_line=1,
                end_line=1,
                modifiers=set(),
                docstring=None,
            )
        ],
    )
    config = CodeConCatConfig()

    result = annotate(parsed_data, config)
    assert "1 symbols" in result.summary
    assert set(result.tags) == {"has_symbols", "python"}
    assert "### Symbols" in result.annotated_content
    assert "- x" in result.annotated_content


def test_disable_symbols():
    parsed_data = ParsedFileData(
        file_path="/path/to/test.py",
        language="python",
        content="x = 1\ny = 2\ndef test(): pass",
        declarations=[
            Declaration(
                kind="symbol",
                name="x",
                start_line=1,
                end_line=1,
                modifiers=set(),
                docstring=None,
            ),
            Declaration(
                kind="symbol",
                name="y",
                start_line=2,
                end_line=2,
                modifiers=set(),
                docstring=None,
            ),
            Declaration(
                kind="function",
                name="test",
                start_line=3,
                end_line=3,
                modifiers=set(),
                docstring=None,
            ),
        ],
    )

    # Test with symbols enabled (default)
    config = CodeConCatConfig(disable_symbols=False)
    result = annotate(parsed_data, config)
    assert "### Symbols" in result.annotated_content
    assert "- x" in result.annotated_content
    assert "- y" in result.annotated_content
    assert "### Functions" in result.annotated_content
    assert "- test" in result.annotated_content

    # Test with symbols disabled
    config = CodeConCatConfig(disable_symbols=True)
    result = annotate(parsed_data, config)
    assert "### Symbols" not in result.annotated_content
    assert "- x" not in result.annotated_content
    assert "- y" not in result.annotated_content
    assert "### Functions" in result.annotated_content
    assert "- test" in result.annotated_content
