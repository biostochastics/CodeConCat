"""Simple tests for XML writer functionality."""

import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

from codeconcat.base_types import CodeConCatConfig, WritableItem
from codeconcat.writer.xml_writer import write_xml


class TestXMLWriterSimple:
    """Simple test suite for XML writer."""

    def test_write_xml_empty(self):
        """Test XML writing with empty items."""
        config = CodeConCatConfig()
        result = write_xml([], config)

        # Should be valid XML
        root = ET.fromstring(result)
        assert root.tag == "codebase_analysis"

        # New structure uses codebase_content
        content_section = root.find("codebase_content")
        assert content_section is not None

    def test_write_xml_single_file(self):
        """Test XML writing with single file."""
        config = CodeConCatConfig()

        # Mock item with XML element
        mock_item = MagicMock(spec=WritableItem)
        mock_item.file_path = "/test/sample.py"

        # Create a mock XML element
        mock_element = ET.Element("file")
        mock_element.set("path", "/test/sample.py")
        ET.SubElement(mock_element, "content").text = "def hello(): pass"

        mock_item.render_xml_element.return_value = mock_element

        result = write_xml([mock_item], config)

        # Should be valid XML
        root = ET.fromstring(result)
        assert root.tag == "codebase_analysis"

        # Check file was included in new structure
        # Files might be under codebase_content or similar
        assert "/test/sample.py" in result

    def test_write_xml_with_repo_overview(self):
        """Test XML writing with repository overview."""
        config = CodeConCatConfig()
        config.include_repo_overview = True
        config.include_directory_structure = True

        folder_tree = "├── src/\n└── README.md"
        result = write_xml([], config, folder_tree)

        _root = ET.fromstring(result)

        # Check for repository overview in new structure
        # May be under metadata or navigation now
        assert "src/" in result or "README.md" in result

    def test_write_xml_with_file_index(self):
        """Test XML writing with file index."""
        config = CodeConCatConfig()
        config.include_file_index = True

        mock_item = MagicMock(spec=WritableItem)
        mock_item.file_path = "/test/file.py"
        mock_element = ET.Element("file")
        mock_item.render_xml_element.return_value = mock_element

        result = write_xml([mock_item], config)

        _root = ET.fromstring(result)

        # Check for file index in new structure
        # May be under navigation or similar
        assert "/test/file.py" in result
