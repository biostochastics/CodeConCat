"""Test symbol indexing functionality."""

import pytest
from codeconcat.base_types import ParsedFileData, Declaration
from codeconcat.symbol_index import SymbolIndex

@pytest.fixture
def sample_parsed_files():
    """Create sample parsed files for testing."""
    return [
        ParsedFileData(
            file_path="/path/to/test1.py",
            content="""
def test_func():
    pass

class TestClass:
    def method(self):
        pass
""",
            language="python",
            declarations=[
                Declaration(
                    kind="function",
                    name="test_func",
                    start_line=2,
                    end_line=3
                ),
                Declaration(
                    kind="class",
                    name="TestClass",
                    start_line=5,
                    end_line=7
                ),
                Declaration(
                    kind="function",
                    name="TestClass.method",
                    start_line=6,
                    end_line=7
                )
            ]
        ),
        ParsedFileData(
            file_path="/path/to/test2.py",
            content="""
from test1 import test_func, TestClass

def another_func():
    test_func()
    tc = TestClass()
    tc.method()
""",
            language="python",
            declarations=[
                Declaration(
                    kind="function",
                    name="another_func",
                    start_line=3,
                    end_line=6
                )
            ]
        )
    ]

def test_build_index(sample_parsed_files):
    """Test building the symbol index."""
    index = SymbolIndex()
    index.build_index(sample_parsed_files)

    # Check that all symbols are indexed
    assert "test_func" in index.symbol_table
    assert "TestClass" in index.symbol_table
    assert "TestClass.method" in index.symbol_table
    assert "another_func" in index.symbol_table

    # Check details of one entry
    test_func_entry = index.symbol_table["test_func"][0]
    assert test_func_entry["file"] == "/path/to/test1.py"
    assert test_func_entry["start_line"] == 2
    assert test_func_entry["end_line"] == 3
    assert test_func_entry["kind"] == "function"

def test_find_references(sample_parsed_files):
    """Test finding references to symbols."""
    index = SymbolIndex()
    index.build_index(sample_parsed_files)
    index.find_references(sample_parsed_files)

    # Print references for debugging
    print("\nAll references:")
    for symbol, refs in index.references.items():
        print(f"\n{symbol}:")
        for ref in refs:
            print(f"  {ref}")

    # Check test_func references
    test_func_refs = index.references["test_func"]
    assert len(test_func_refs) == 2  # Import and usage
    assert any(r["line"] == 2 for r in test_func_refs)  # Import line
    assert any(r["line"] == 5 for r in test_func_refs)  # Usage line

    # Check TestClass references
    test_class_refs = index.references["TestClass"]
    assert len(test_class_refs) == 2  # Import and usage
    assert any(r["line"] == 2 for r in test_class_refs)  # Import line
    assert any(r["line"] == 6 for r in test_class_refs)  # Usage line

def test_empty_references():
    """Test handling of non-existent symbol references."""
    index = SymbolIndex()
    assert index.references.get("nonexistent") is None

def test_multiple_declarations():
    """Test handling of multiple declarations of the same symbol."""
    files = [
        ParsedFileData(
            file_path="/path/to/test1.py",
            content="def func(): pass",
            language="python",
            declarations=[
                Declaration(
                    kind="function",
                    name="func",
                    start_line=1,
                    end_line=1
                )
            ]
        ),
        ParsedFileData(
            file_path="/path/to/test2.py",
            content="def func(): return True",
            language="python",
            declarations=[
                Declaration(
                    kind="function",
                    name="func",
                    start_line=1,
                    end_line=1
                )
            ]
        )
    ]

    index = SymbolIndex()
    index.build_index(files)

    # Check that both declarations are recorded
    assert len(index.symbol_table["func"]) == 2
    files = {entry["file"] for entry in index.symbol_table["func"]}
    assert files == {"/path/to/test1.py", "/path/to/test2.py"}
