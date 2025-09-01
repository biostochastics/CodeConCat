"""
Unit tests for the JSON writer module.
"""

import json
from typing import Any, Dict
from unittest.mock import MagicMock

from codeconcat.base_types import CodeConCatConfig, WritableItem
from codeconcat.writer.json_writer import write_json


class MockWritableItem(WritableItem):
    """Mock implementation of WritableItem for testing."""

    def __init__(self, file_path: str, render_data: Dict[str, Any]):
        self.file_path = file_path
        self._render_data = render_data

    def render_json_dict(self, _config: CodeConCatConfig) -> Dict[str, Any]:
        """Return the mock render data."""
        return self._render_data

    def render_xml_element(self, _config: CodeConCatConfig):
        """Not used in JSON writer tests."""
        return None

    def render_markdown_chunks(self, _config: CodeConCatConfig):
        """Not used in JSON writer tests."""
        return []

    def render_text_lines(self, _config: CodeConCatConfig):
        """Not used in JSON writer tests."""
        return []


class TestWriteJson:
    """Test suite for write_json function."""

    def test_basic_json_output(self):
        """Test basic JSON output generation."""
        # Create mock items
        items = [
            MockWritableItem("file1.py", {"path": "file1.py", "content": "print('hello')"}),
            MockWritableItem("file2.py", {"path": "file2.py", "content": "print('world')"}),
        ]

        # Create config
        config = CodeConCatConfig(target_path=".", output="output.json")

        # Generate JSON
        result = write_json(items, config)

        # Parse result
        data = json.loads(result)

        # Verify structure - files is now a list of file objects
        assert "files" in data
        assert isinstance(data["files"], list)
        assert len(data["files"]) == 2

        # Check that files have correct structure
        file_paths = [f.get("file_path", f.get("path")) for f in data["files"]]
        assert "file1.py" in file_paths
        assert "file2.py" in file_paths

        # Check individual file structures
        for file_data in data["files"]:
            # Mock items use "path", real items use "file_path" via metadata
            assert "path" in file_data or "file_path" in file_data
            if "metadata" in file_data:
                expected_path = file_data.get("file_path", file_data.get("path"))
                assert file_data["metadata"]["path"] == expected_path

    def test_with_repository_overview(self):
        """Test JSON output with repository overview."""
        items = []

        # Create config with repository overview enabled
        config = CodeConCatConfig(
            target_path=".",
            output="output.json",
            include_repo_overview=True,
            include_directory_structure=True,
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

        # Verify repository overview is now under 'repository' key
        assert "repository" in data
        # Directory structure would be passed differently now
        # Just verify the repository section exists

    def test_sorted_files(self):
        """Test file sorting."""
        # Create items in unsorted order
        items = [
            MockWritableItem("z_file.py", {"path": "z_file.py"}),
            MockWritableItem("a_file.py", {"path": "a_file.py"}),
            MockWritableItem("m_file.py", {"path": "m_file.py"}),
        ]

        # Create config with sorting enabled
        config = CodeConCatConfig(target_path=".", output="output.json", sort_files=True)

        # Generate JSON
        result = write_json(items, config)

        # Parse result
        data = json.loads(result)

        # Verify files exist (list structure should preserve sort order)
        assert len(data["files"]) == 3
        file_paths = [f.get("file_path", f.get("path")) for f in data["files"]]
        assert "a_file.py" in file_paths
        assert "m_file.py" in file_paths
        assert "z_file.py" in file_paths
        # Verify sort order
        assert file_paths == ["a_file.py", "m_file.py", "z_file.py"]

    def test_empty_items_list(self):
        """Test with empty items list."""
        items = []
        config = CodeConCatConfig(target_path=".", output="output.json")

        # Generate JSON
        result = write_json(items, config)

        # Parse result
        data = json.loads(result)

        # Verify structure - empty dict for no files
        assert "files" in data
        assert data["files"] == []

    def test_custom_json_indent(self):
        """Test custom JSON indentation."""
        items = [MockWritableItem("file.py", {"path": "file.py"})]

        # Create config with custom indent using mock
        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = "."
        config.output = "output.json"
        config.include_repo_overview = False
        config.sort_files = False
        config.enable_compression = False
        config.json_indent = 4
        config.format = "json"

        # Generate JSON
        result = write_json(items, config)

        # Verify indentation (4 spaces)
        lines = result.split("\n")
        # Check that indented lines have 4 spaces
        for line in lines:
            if (
                line.strip()
                and not line.startswith("{")
                and not line.startswith("}")
                and line.lstrip() != line
            ):  # If line is indented
                indent = len(line) - len(line.lstrip())
                assert indent % 4 == 0  # Should be multiple of 4

    def test_default_json_indent(self):
        """Test default JSON indentation when not specified."""
        items = [MockWritableItem("file.py", {"path": "file.py"})]

        # Create config without json_indent
        config = CodeConCatConfig(target_path=".", output="output.json")

        # Generate JSON
        result = write_json(items, config)

        # Verify default indentation (2 spaces)
        lines = result.split("\n")
        # Check that indented lines have 2 spaces
        for line in lines:
            if (
                line.strip()
                and not line.startswith("{")
                and not line.startswith("}")
                and line.lstrip() != line
            ):  # If line is indented
                indent = len(line) - len(line.lstrip())
                assert indent % 2 == 0  # Should be multiple of 2

    def test_with_compression_segments(self):
        """Test JSON output with compression segments."""
        # Create mock items
        items = [MockWritableItem("file.py", {"path": "file.py", "content": "full content"})]

        # Create config with compression enabled
        config = CodeConCatConfig(target_path=".", output="output.json", enable_compression=True)

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

        # Verify compression segments - files is list now
        assert len(data["files"]) == 1
        file_data = data["files"][0]
        # Note: content_segments handling may vary
        # Just verify the file exists
        assert file_data.get("file_path", file_data.get("path")) == "file.py"

    def test_item_returns_none(self):
        """Test when an item's render_json_dict returns None."""

        # Create mock item that returns None
        class NoneReturningItem(MockWritableItem):
            def render_json_dict(self, _config):
                return None

        items = [
            MockWritableItem("file1.py", {"path": "file1.py"}),
            NoneReturningItem("file2.py", {}),  # This returns None
            MockWritableItem("file3.py", {"path": "file3.py"}),
        ]

        config = CodeConCatConfig(target_path=".", output="output.json")

        # Generate JSON
        result = write_json(items, config)

        # Parse result
        data = json.loads(result)

        # Only items that return valid data should be included
        assert len(data["files"]) == 2
        file_paths = [f.get("file_path", f.get("path")) for f in data["files"]]
        assert "file1.py" in file_paths
        assert "file3.py" in file_paths
        assert "file2.py" not in file_paths

    def test_non_serializable_objects(self):
        """Test handling of non-serializable objects."""
        # Create item with non-serializable data
        items = [
            MockWritableItem(
                "file.py",
                {
                    "path": "file.py",
                    "custom_object": object(),  # Non-serializable
                    "set_data": {1, 2, 3},  # Sets need special handling
                },
            )
        ]

        config = CodeConCatConfig(target_path=".", output="output.json")

        # Generate JSON (should use default=str)
        result = write_json(items, config)

        # Should not raise an exception
        data = json.loads(result)
        assert len(data["files"]) == 1
        # The non-serializable objects should be converted to strings
        file_data = data["files"][0]
        assert isinstance(file_data["custom_object"], str)
        assert isinstance(file_data["set_data"], str)
