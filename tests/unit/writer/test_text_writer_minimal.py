"""Minimal tests for text writer functionality."""

import pytest
from unittest.mock import MagicMock

from codeconcat.writer.text_writer import write_text
from codeconcat.base_types import CodeConCatConfig, WritableItem


class TestTextWriterMinimal:
    """Minimal test suite for text writer."""

    def test_write_text_empty(self):
        """Test writing empty items list."""
        config = CodeConCatConfig()
        result = write_text([], config)
        
        assert result
        assert isinstance(result, str)
        assert "File Content" in result

    def test_write_text_single_file(self):
        """Test writing single file."""
        config = CodeConCatConfig()
        
        mock_item = MagicMock(spec=WritableItem)
        mock_item.file_path = "/test/sample.py"
        mock_item.render_text_lines.return_value = ["def hello():", "    pass"]
        
        result = write_text([mock_item], config)
        
        assert "sample.py" in result
        assert "def hello():" in result
        assert "pass" in result

    def test_write_text_with_repo_overview(self):
        """Test writing with repository overview."""
        config = CodeConCatConfig()
        config.include_repo_overview = True
        config.include_directory_structure = True
        
        folder_tree = "├── src/\n└── README.md"
        result = write_text([], config, folder_tree)
        
        assert "Repository Overview" in result
        assert "src/" in result

    def test_write_text_with_file_index(self):
        """Test writing with file index."""
        config = CodeConCatConfig()
        config.include_file_index = True
        
        mock_item = MagicMock(spec=WritableItem)
        mock_item.file_path = "/test/file.py"
        mock_item.render_text_lines.return_value = ["content"]
        
        result = write_text([mock_item], config)
        
        assert "File Index" in result
        assert "1. /test/file.py" in result