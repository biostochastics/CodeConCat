import os
import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.collector.local_collector import (
    collect_local_files,
    process_file,
    should_skip_dir,
    should_include_file,
    matches_pattern,
    ext_map,
    is_binary_file
)

@pytest.fixture
def complex_dir_structure(tmp_path):
    """Create a complex directory structure for testing."""
    # Create main directories
    src = tmp_path / "src"
    tests = tmp_path / "tests"
    docs = tmp_path / "docs"
    hidden = tmp_path / ".hidden"
    
    for dir in [src, tests, docs, hidden]:
        dir.mkdir()

    # Create various file types
    (src / "main.py").write_text("def main(): pass")
    (src / "utils.py").write_text("def util(): pass")
    (tests / "test_main.py").write_text("def test_main(): pass")
    (docs / "README.md").write_text("# Documentation")
    (hidden / "cache.tmp").write_text("cache data")
    
    # Create nested structure
    nested = src / "nested" / "deep"
    nested.mkdir(parents=True)
    (nested / "nested.py").write_text("nested = True")
    
    # Create binary-like file
    with open(str(tmp_path / "binary.bin"), "wb") as f:
        f.write(bytes(range(256)))
    
    return tmp_path

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

def test_collect_local_files_comprehensive(complex_dir_structure, basic_config):
    """Test collecting files with various configurations."""
    config = basic_config
    config.target_path = str(complex_dir_structure)
    
    # Test with default config
    files = collect_local_files(str(complex_dir_structure), config)
    assert len(files) > 0
    assert any(f.file_path.endswith("main.py") for f in files)
    assert any(f.file_path.endswith("README.md") for f in files)
    
    # Test with docs disabled
    config.extract_docs = False
    files = collect_local_files(str(complex_dir_structure), config)
    assert not any(f.file_path.endswith(".md") for f in files)
    
    # Test with custom includes
    config.include_paths = ["**/*.py"]
    files = collect_local_files(str(complex_dir_structure), config)
    assert all(f.file_path.endswith(".py") for f in files)
    
    # Test with custom excludes
    config.exclude_paths = ["**/nested/**"]
    files = collect_local_files(str(complex_dir_structure), config)
    assert not any("nested" in f.file_path for f in files)

@pytest.mark.asyncio
async def test_process_file_with_various_content(tmp_path, basic_config):
    """Test processing files with different content types."""
    # Test Python file
    py_file = tmp_path / "test.py"
    py_file.write_text("def test():\n    # Comment\n    pass\n")
    result = process_file(str(py_file), basic_config)
    assert result.language == "python"
    assert "def test()" in result.content
    
    # Test empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    result = process_file(str(empty_file), basic_config)
    assert result.content == ""
    
    # Test file with special characters
    special_file = tmp_path / "special.txt"
    special_file.write_text("Hello\n世界\n🌍")
    result = process_file(str(special_file), basic_config)
    assert "Hello" in result.content
    assert "世界" in result.content
    assert "🌍" in result.content

def test_should_skip_dir_patterns():
    """Test directory skipping logic with various patterns."""
    assert should_skip_dir(".git", [])  # Default excludes
    assert should_skip_dir("node_modules", [])  # Default excludes
    assert not should_skip_dir("src", [])
    assert should_skip_dir("test_dir", ["test_*"])
    assert should_skip_dir("path/to/excluded", ["**/excluded"])
    assert not should_skip_dir("path/to/included", ["**/excluded"])

def test_should_include_file_comprehensive(basic_config):
    """Test file inclusion logic with various patterns and edge cases."""
    # Test basic extensions
    assert should_include_file("test.py", basic_config)
    assert should_include_file("test.md", basic_config)
    assert not should_include_file("test.pyc", basic_config)
    
    # Test with custom includes
    config = basic_config
    config.include_paths = ["*.txt"]
    assert should_include_file("test.txt", config)
    assert not should_include_file("test.py", config)
    
    # Test with both includes and excludes
    config.include_paths = ["*.py"]
    config.exclude_paths = ["test_*.py"]
    assert should_include_file("main.py", config)
    assert not should_include_file("test_main.py", config)

def test_matches_pattern_edge_cases():
    """Test pattern matching with various edge cases."""
    assert matches_pattern("test.py", "*.py")
    assert matches_pattern("path/to/test.py", "**/*.py")
    assert matches_pattern(".hidden", ".*")
    assert not matches_pattern("test.py", "*.txt")
    assert matches_pattern("path/to/test.txt", "**/test.txt")
    assert matches_pattern("TEST.PY", "*.py")  # Case insensitive

def test_ext_map_comprehensive(basic_config):
    """Test extension mapping with various file types."""
    assert ext_map(".py", basic_config) == "python"
    assert ext_map(".md", basic_config) == "markdown"
    assert ext_map(".unknown", basic_config) == "text"
    assert ext_map("", basic_config) == "text"
    
    # Test with custom mappings
    config = basic_config
    config.custom_extension_map = {".custom": "customlang"}
    assert ext_map(".custom", config) == "customlang"

def test_is_binary_file_various_types(tmp_path):
    """Test binary file detection with various file types."""
    # Test text file
    text_file = tmp_path / "text.txt"
    text_file.write_text("Hello, World!")
    assert not is_binary_file(str(text_file))
    
    # Test binary file
    binary_file = tmp_path / "binary.bin"
    with open(str(binary_file), "wb") as f:
        f.write(bytes(range(256)))
    assert is_binary_file(str(binary_file))
    
    # Test empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    assert not is_binary_file(str(empty_file))
