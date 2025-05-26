"""Simple tests for XML writer functionality."""

from unittest.mock import MagicMock
import xml.etree.ElementTree as ET

from codeconcat.writer.xml_writer import write_xml
from codeconcat.base_types import CodeConCatConfig, WritableItem


class TestXMLWriterSimple:
    """Simple test suite for XML writer."""

    def test_write_xml_empty(self):
        """Test XML writing with empty items."""
        config = CodeConCatConfig()
        result = write_xml([], config)

        # Should be valid XML
        root = ET.fromstring(result)
        assert root.tag == "codeconcat_output"

        files_section = root.find("files")
        assert files_section is not None
        assert len(files_section) == 0

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
        assert root.tag == "codeconcat_output"

        # Check file was included
        file_elem = root.find(".//file[@path='/test/sample.py']")
        assert file_elem is not None

    def test_write_xml_with_repo_overview(self):
        """Test XML writing with repository overview."""
        config = CodeConCatConfig()
        config.include_repo_overview = True
        config.include_directory_structure = True

        folder_tree = "├── src/\n└── README.md"
        result = write_xml([], config, folder_tree)

        root = ET.fromstring(result)

        # Check for repository overview
        repo_overview = root.find("repository_overview")
        assert repo_overview is not None

        # Check for directory structure
        tree_elem = root.find(".//directory_structure")
        assert tree_elem is not None
        assert "src/" in tree_elem.text

    def test_write_xml_with_file_index(self):
        """Test XML writing with file index."""
        config = CodeConCatConfig()
        config.include_file_index = True

        mock_item = MagicMock(spec=WritableItem)
        mock_item.file_path = "/test/file.py"
        mock_element = ET.Element("file")
        mock_item.render_xml_element.return_value = mock_element

        result = write_xml([mock_item], config)

        root = ET.fromstring(result)

        # Check for file index
        file_index = root.find("file_index")
        assert file_index is not None
        assert len(file_index.findall("file")) == 1
        assert file_index.find("file").get("path") == "/test/file.py"
