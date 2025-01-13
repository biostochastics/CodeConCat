import os
import pytest
from pathlib import Path
from unittest.mock import patch

from codeconcat.base_types import CodeConCatConfig
from codeconcat.main import run_codeconcat
from codeconcat.collector.local_collector import collect_local_files
from codeconcat.processor.content_processor import process_file_content

@pytest.fixture
def complex_project(tmp_path):
    """Create a complex project structure for integration testing."""
    # Create directory structure
    src = tmp_path / "src"
    tests = tmp_path / "tests"
    docs = tmp_path / "docs"
    config = tmp_path / "config"
    
    for dir in [src, tests, docs, config]:
        dir.mkdir()

    # Create source files with realistic content
    (src / "main.py").write_text("""
import os
from typing import List

def process_files(paths: List[str]) -> None:
    '''Process multiple files.'''
    for path in paths:
        if os.path.exists(path):
            process_single_file(path)

def process_single_file(path: str) -> None:
    '''Process a single file.'''
    with open(path, 'r') as f:
        content = f.read()
    # TODO: Implement processing
    pass
""")

    (src / "utils.py").write_text("""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def setup_logging(level: Optional[str] = None) -> None:
    '''Setup logging configuration.'''
    if level is None:
        level = 'INFO'
    logging.basicConfig(level=level)
    logger.debug('Logging configured')
""")

    # Create test files
    (tests / "test_main.py").write_text("""
import pytest
from src.main import process_files

def test_process_files():
    '''Test file processing.'''
    with pytest.raises(FileNotFoundError):
        process_files(['nonexistent.txt'])
""")

    # Create documentation
    (docs / "README.md").write_text("""
# Project Documentation

## Overview
This is a test project for integration testing.

## Usage
```python
from src.main import process_files
process_files(['example.txt'])
```
""")

    # Create configuration
    (config / "settings.json").write_text("""
{
    "processing": {
        "max_file_size": 1048576,
        "supported_extensions": [".txt", ".py", ".md"],
        "ignore_patterns": ["*.pyc", "__pycache__"]
    }
}
""")

    return tmp_path

def test_full_integration_flow(complex_project):
    """Test the entire flow from collection to processing."""
    config = CodeConCatConfig(
        target_path=str(complex_project),
        github_url=None,
        github_token=None,
        github_ref=None,
        include_languages=[],
        exclude_languages=[],
        include_paths=[],
        exclude_paths=[],
        extract_docs=True,
        merge_docs=True,
        output=str(complex_project / "output.md"),
        format="markdown",
        max_workers=4,
        disable_tree=False,
        disable_copy=False,
        disable_annotations=False,
        disable_symbols=False,
        disable_ai_context=False
    )
    
    # Run the complete flow
    run_codeconcat(config)
    
    # Verify output file exists and contains expected content
    output_path = complex_project / "output.md"
    assert output_path.exists()
    content = output_path.read_text()
    
    # Check for presence of various components
    assert "# Project Documentation" in content  # README content
    assert "def process_files" in content  # Source code
    assert "def test_process_files" in content  # Test code
    assert '"processing"' in content  # Config content

def test_incremental_processing(complex_project):
    """Test processing files incrementally with different configurations."""
    # First pass: Process only Python files
    config = CodeConCatConfig(
        target_path=str(complex_project),
        github_url=None,
        github_token=None,
        github_ref=None,
        include_languages=[],
        exclude_languages=[],
        include_paths=["**/*.py"],
        exclude_paths=[],
        extract_docs=False,
        merge_docs=False,
        output=str(complex_project / "output_py.md"),
        format="markdown",
        max_workers=4,
        disable_tree=False,
        disable_copy=False,
        disable_annotations=False,
        disable_symbols=False,
        disable_ai_context=False
    )
    
    files = collect_local_files(str(complex_project), config)
    assert all(f.file_path.endswith('.py') for f in files)
    assert len(files) > 0
    
    # Second pass: Process only documentation
    config.extract_docs = True
    config.include_paths = ["**/*.md"]
    config.output = str(complex_project / "output_docs.md")
    
    files = collect_local_files(str(complex_project), config)
    assert all(f.file_path.endswith('.md') for f in files)
    assert len(files) > 0

@pytest.mark.asyncio
async def test_concurrent_processing(complex_project):
    """Test processing multiple files concurrently."""
    config = CodeConCatConfig(
        target_path=str(complex_project),
        github_url=None,
        github_token=None,
        github_ref=None,
        include_languages=[],
        exclude_languages=[],
        include_paths=[],
        exclude_paths=[],
        extract_docs=True,
        merge_docs=True,
        output=str(complex_project / "output_concurrent.md"),
        format="markdown",
        max_workers=4,
        disable_tree=False,
        disable_copy=False,
        disable_annotations=False,
        disable_symbols=False,
        disable_ai_context=False
    )
    
    # Collect files
    files = collect_local_files(str(complex_project), config)
    
    # Process files concurrently
    processed_contents = []
    for file_data in files:
        if file_data.content:
            processed_content = process_file_content(file_data.content, config)
            processed_contents.append(processed_content)
    
    assert len(processed_contents) > 0
    assert all(isinstance(content, str) for content in processed_contents)

def test_error_handling(complex_project):
    """Test error handling in the integration flow."""
    # Test with invalid path
    config = CodeConCatConfig(
        target_path="/nonexistent/path",
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
    
    with pytest.raises(Exception):
        run_codeconcat(config)
    
    # Test with invalid output path
    config = CodeConCatConfig(
        target_path=str(complex_project),
        github_url=None,
        github_token=None,
        github_ref=None,
        include_languages=[],
        exclude_languages=[],
        include_paths=[],
        exclude_paths=[],
        extract_docs=True,
        merge_docs=True,
        output="/invalid/path/output.md",
        format="markdown",
        max_workers=4,
        disable_tree=False,
        disable_copy=False,
        disable_annotations=False,
        disable_symbols=False,
        disable_ai_context=False
    )
    
    with pytest.raises(Exception):
        run_codeconcat(config)

def test_large_file_handling(complex_project):
    """Test handling of large files."""
    # Create a large file
    large_file = complex_project / "src" / "large_file.py"
    large_content = "x = 1\n" * 10000  # Create a large file
    large_file.write_text(large_content)
    
    config = CodeConCatConfig(
        target_path=str(complex_project),
        github_url=None,
        github_token=None,
        github_ref=None,
        include_languages=[],
        exclude_languages=[],
        include_paths=[],
        exclude_paths=[],
        extract_docs=True,
        merge_docs=True,
        output=str(complex_project / "output_large.md"),
        format="markdown",
        max_workers=4,
        disable_tree=False,
        disable_copy=False,
        disable_annotations=False,
        disable_symbols=False,
        disable_ai_context=False
    )
    
    # Process should handle large file without memory issues
    run_codeconcat(config)
    assert (complex_project / "output_large.md").exists()
