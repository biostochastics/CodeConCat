"""
Unit tests for the JSON writer module.
"""

import json
import pytest
from unittest.mock import MagicMock, Mock
from typing import Dict, Any

from codeconcat.writer.json_writer import write_json
from codeconcat.base_types import CodeConCatConfig, WritableItem


class MockWritableItem(WritableItem):
    """Mock implementation of WritableItem for testing."""
    
    def __init__(self, file_path: str, render_data: Dict[str, Any]):
        self.file_path = file_path
        self._render_data = render_data
    
    def render_json_dict(self, config: CodeConCatConfig) -> Dict[str, Any]:
        """Return the mock render data."""
        return self._render_data
    
    def render_xml_element(self, config: CodeConCatConfig):
        """Not used in JSON writer tests."""
        return None
    
    def render_markdown_chunks(self, config: CodeConCatConfig):
        """Not used in JSON writer tests."""
        return []
    
    def render_text_lines(self, config: CodeConCatConfig):
        """Not used in JSON writer tests."""
        return []


class TestWriteJson:
    """Test suite for write_json function."""

    def test_basic_json_output(self):
        """Test basic JSON output generation."""
        # Create mock items
        items = [
            MockWritableItem("file1.py", {"path": "file1.py", "content": "print('hello')"}),
            MockWritableItem("file2.py", {"path": "file2.py", "content": "print('world')"})
        ]
        
        # Create config
        config = CodeConCatConfig(
            target_path=".",
            output="output.json"
        )
        
        # Generate JSON
        result = write_json(items, config)
        
        # Parse result
        data = json.loads(result)
        
        # Verify structure
        assert "files" in data
        assert len(data["files"]) == 2
        assert data["files"][0]["path"] == "file1.py"
        assert data["files"][1]["path"] == "file2.py"

    def test_with_repository_overview(self):
        """Test JSON output with repository overview."""
        items = []
        
        # Create config with repository overview enabled
        config = CodeConCatConfig(
            target_path=".",
            output="output.json",
            include_repo_overview=True,
            include_directory_structure=True
        )
        
        folder_tree = """
project/
├── src/
│   └── main.py
└── tests/
    └── test_main.py
        """
        
        # Generate JSON
        result = write_json(items, config, folder_tree_str=folder_tree)
        
        # Parse result
        data = json.loads(result)
        
        # Verify repository overview
        assert "repository_overview" in data
        assert "directory_structure" in data["repository_overview"]
        assert "project/" in data["repository_overview"]["directory_structure"]

    def test_sorted_files(self):
        """Test file sorting."""
        # Create items in unsorted order
        items = [
            MockWritableItem("z_file.py", {"path": "z_file.py"}),
            MockWritableItem("a_file.py", {"path": "a_file.py"}),
            MockWritableItem("m_file.py", {"path": "m_file.py"})
        ]
        
        # Create config with sorting enabled
        config = CodeConCatConfig(
            target_path=".",
            output="output.json",
            sort_files=True
        )
        
        # Generate JSON
        result = write_json(items, config)
        
        # Parse result
        data = json.loads(result)
        
        # Verify files are sorted
        assert len(data["files"]) == 3
        assert data["files"][0]["path"] == "a_file.py"
        assert data["files"][1]["path"] == "m_file.py"
        assert data["files"][2]["path"] == "z_file.py"

    def test_empty_items_list(self):
        """Test with empty items list."""
        items = []
        config = CodeConCatConfig(target_path=".", output="output.json")
        
        # Generate JSON
        result = write_json(items, config)
        
        # Parse result
        data = json.loads(result)
        
        # Verify structure
        assert "files" in data
        assert data["files"] == []

    def test_custom_json_indent(self):
        """Test custom JSON indentation."""
        items = [
            MockWritableItem("file.py", {"path": "file.py"})
        ]
        
        # Create config with custom indent using mock
        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = "."
        config.output = "output.json"
        config.include_repo_overview = False
        config.sort_files = False
        config.enable_compression = False
        config.json_indent = 4
        
        # Generate JSON
        result = write_json(items, config)
        
        # Verify indentation (4 spaces)
        lines = result.split('\n')
        # Check that indented lines have 4 spaces
        for line in lines:
            if line.strip() and not line.startswith('{') and not line.startswith('}'):
                if line.lstrip() != line:  # If line is indented
                    indent = len(line) - len(line.lstrip())
                    assert indent % 4 == 0  # Should be multiple of 4

    def test_default_json_indent(self):
        """Test default JSON indentation when not specified."""
        items = [
            MockWritableItem("file.py", {"path": "file.py"})
        ]
        
        # Create config without json_indent
        config = CodeConCatConfig(
            target_path=".",
            output="output.json"
        )
        
        # Generate JSON
        result = write_json(items, config)
        
        # Verify default indentation (2 spaces)
        lines = result.split('\n')
        # Check that indented lines have 2 spaces
        for line in lines:
            if line.strip() and not line.startswith('{') and not line.startswith('}'):
                if line.lstrip() != line:  # If line is indented
                    indent = len(line) - len(line.lstrip())
                    assert indent % 2 == 0  # Should be multiple of 2

    def test_with_compression_segments(self):
        """Test JSON output with compression segments."""
        # Create mock items
        items = [
            MockWritableItem("file.py", {"path": "file.py", "content": "full content"})
        ]
        
        # Create config with compression enabled
        config = CodeConCatConfig(
            target_path=".",
            output="output.json",
            enable_compression=True
        )
        
        # Mock compressed segments
        mock_segment = MagicMock()
        mock_segment.segment_type.value = "code"
        mock_segment.start_line = 1
        mock_segment.end_line = 10
        mock_segment.content = "compressed content"
        mock_segment.metadata = {"key": "value"}
        
        config._compressed_segments = [mock_segment]
        
        # Generate JSON
        result = write_json(items, config)
        
        # Parse result
        data = json.loads(result)
        
        # Verify compression segments
        assert len(data["files"]) == 1
        assert "content_segments" in data["files"][0]
        segments = data["files"][0]["content_segments"]
        assert len(segments) == 1
        assert segments[0]["type"] == "code"
        assert segments[0]["start_line"] == 1
        assert segments[0]["end_line"] == 10
        assert segments[0]["content"] == "compressed content"
        assert segments[0]["metadata"] == {"key": "value"}

    def test_item_returns_none(self):
        """Test when an item's render_json_dict returns None."""
        # Create mock item that returns None
        class NoneReturningItem(MockWritableItem):
            def render_json_dict(self, config):
                return None
        
        items = [
            MockWritableItem("file1.py", {"path": "file1.py"}),
            NoneReturningItem("file2.py", {}),  # This returns None
            MockWritableItem("file3.py", {"path": "file3.py"})
        ]
        
        config = CodeConCatConfig(target_path=".", output="output.json")
        
        # Generate JSON
        result = write_json(items, config)
        
        # Parse result
        data = json.loads(result)
        
        # Only items that return valid data should be included
        assert len(data["files"]) == 2
        assert data["files"][0]["path"] == "file1.py"
        assert data["files"][1]["path"] == "file3.py"

    def test_non_serializable_objects(self):
        """Test handling of non-serializable objects."""
        # Create item with non-serializable data
        items = [
            MockWritableItem("file.py", {
                "path": "file.py",
                "custom_object": object(),  # Non-serializable
                "set_data": {1, 2, 3}  # Sets need special handling
            })
        ]
        
        config = CodeConCatConfig(target_path=".", output="output.json")
        
        # Generate JSON (should use default=str)
        result = write_json(items, config)
        
        # Should not raise an exception
        data = json.loads(result)
        assert len(data["files"]) == 1
        # The non-serializable objects should be converted to strings
        assert isinstance(data["files"][0]["custom_object"], str)
        assert isinstance(data["files"][0]["set_data"], str)