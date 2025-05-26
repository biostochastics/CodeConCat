"""Comprehensive tests for XML writer functionality."""

import pytest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from codeconcat.writer.xml_writer import write_xml
from codeconcat.base_types import (
    CodeConCatConfig,
    WritableItem,
    AnnotatedFileData,
    ParsedDocData,
    ContentSegment,
    ContentSegmentType,
    Declaration,
)


class TestXMLWriter:
    """Test XML writer functionality."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = CodeConCatConfig()
        config.include_repo_overview = True
        config.include_directory_structure = True
        config.include_file_index = True
        config.sort_files = False
        config.enable_compression = False
        config.output = "output.xml"
        return config

    @pytest.fixture
    def sample_file(self):
        """Create a sample annotated file."""
        return AnnotatedFileData(
            file_path="/test/sample.py",
            content='def hello():\n    print("Hello, World!")',
            annotated_content='def hello():\n    print("Hello, World!")',
            language="python",
            declarations=[Declaration(kind="function", name="hello", start_line=1, end_line=2)],
            imports=["os", "sys"],
        )

    @pytest.fixture
    def sample_doc(self):
        """Create a sample documentation item."""
        return ParsedDocData(
            file_path="/test/README.md",
            content="# Test Project\n\nThis is a test.",
            doc_type="markdown",
            summary="Test project documentation",
        )

    def test_write_xml_basic(self, config, sample_file):
        """Test basic XML writing."""
        items = [sample_file]
        result = write_xml(items, config)

        # Parse the result
        root = ET.fromstring(result)

        # Check root element
        assert root.tag == "codeconcat_output"

        # Check repository overview
        repo_overview = root.find("repository_overview")
        assert repo_overview is not None

        # Check file index
        file_index = root.find("file_index")
        assert file_index is not None
        assert len(file_index.findall("file")) == 1
        assert file_index.find("file").get("path") == "/test/sample.py"

        # Check files section
        files_section = root.find("files")
        assert files_section is not None
        assert len(files_section.findall("file")) == 1

    def test_write_xml_with_folder_tree(self, config, sample_file):
        """Test XML writing with folder tree."""
        items = [sample_file]
        folder_tree = "├── src/\n│   └── main.py\n└── README.md"

        result = write_xml(items, config, folder_tree)
        root = ET.fromstring(result)

        # Check directory structure
        tree_elem = root.find(".//directory_structure")
        assert tree_elem is not None
        assert folder_tree in tree_elem.text

    def test_write_xml_without_repo_overview(self, config, sample_file):
        """Test XML writing without repository overview."""
        config.include_repo_overview = False
        items = [sample_file]

        result = write_xml(items, config)
        root = ET.fromstring(result)

        # Repository overview should not be present
        repo_overview = root.find("repository_overview")
        assert repo_overview is None

    def test_write_xml_without_file_index(self, config, sample_file):
        """Test XML writing without file index."""
        config.include_file_index = False
        items = [sample_file]

        result = write_xml(items, config)
        root = ET.fromstring(result)

        # File index should not be present
        file_index = root.find("file_index")
        assert file_index is None

    def test_write_xml_with_sorted_files(self, config):
        """Test XML writing with sorted files."""
        config.sort_files = True

        file1 = AnnotatedFileData(
            file_path="/test/b_file.py",
            content="content1",
            annotated_content="content1",
            language="python",
        )
        file2 = AnnotatedFileData(
            file_path="/test/a_file.py",
            content="content2",
            annotated_content="content2",
            language="python",
        )

        items = [file1, file2]
        result = write_xml(items, config)
        root = ET.fromstring(result)

        # Check file order in index
        file_index = root.find("file_index")
        files = file_index.findall("file")
        assert files[0].get("path") == "/test/a_file.py"
        assert files[1].get("path") == "/test/b_file.py"

    def test_write_xml_with_mixed_items(self, config, sample_file, sample_doc):
        """Test XML writing with mixed file and documentation items."""
        items = [sample_file, sample_doc]

        result = write_xml(items, config)
        root = ET.fromstring(result)

        # Check files section contains both items
        files_section = root.find("files")
        assert len(files_section) == 2

        # Check file index
        file_index = root.find("file_index")
        assert len(file_index.findall("file")) == 2

    def test_write_xml_with_compression(self, config, sample_file):
        """Test XML writing with compression enabled."""
        config.enable_compression = True

        # Mock compressed segments
        segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="def hello():\n    print('Hello')",
            start_line=1,
            end_line=2,
            metadata={"name": "hello"},
        )
        config._compressed_segments = {sample_file.file_path: [segment]}

        items = [sample_file]
        result = write_xml(items, config)
        root = ET.fromstring(result)

        # Should still produce valid XML with compression enabled
        assert root.tag == "codeconcat_output"
        files_section = root.find("files")
        assert files_section is not None
        assert len(files_section) > 0

    def test_write_xml_empty_items(self, config):
        """Test XML writing with empty items list."""
        items = []
        result = write_xml(items, config)
        root = ET.fromstring(result)

        # Should still have structure
        assert root.tag == "codeconcat_output"
        files_section = root.find("files")
        assert files_section is not None
        assert len(files_section) == 0

    def test_write_xml_with_special_characters(self, config):
        """Test XML writing with special characters in content."""
        file_with_special = AnnotatedFileData(
            file_path="/test/special.py",
            content='print("< > & \' " symbols")',
            annotated_content='print("< > & \' " symbols")',
            language="python",
        )

        items = [file_with_special]
        result = write_xml(items, config)

        # Should be valid XML
        root = ET.fromstring(result)
        assert root is not None

    def test_write_xml_pretty_print_fallback(self, config, sample_file):
        """Test XML writing when pretty print fails."""
        items = [sample_file]

        # Mock minidom to raise exception
        with patch("xml.dom.minidom.parseString") as mock_parse:
            mock_parse.side_effect = Exception("Pretty print failed")

            result = write_xml(items, config)

            # Should still return valid XML
            root = ET.fromstring(result)
            assert root.tag == "codeconcat_output"

    def test_write_xml_with_unicode_content(self, config):
        """Test XML writing with unicode content."""
        file_with_unicode = AnnotatedFileData(
            file_path="/test/unicode.py",
            content='print("Hello 世界 🌍")',
            annotated_content='print("Hello 世界 🌍")',
            language="python",
        )

        items = [file_with_unicode]
        result = write_xml(items, config)

        # Should handle unicode properly
        root = ET.fromstring(result)
        assert root is not None

    def test_write_xml_render_delegation(self, config):
        """Test that XML writing properly delegates to item's render_xml_element."""
        mock_item = Mock(spec=WritableItem)
        mock_item.file_path = "/test/mock.py"

        mock_element = ET.Element("file")
        mock_element.set("path", "/test/mock.py")
        mock_item.render_xml_element.return_value = mock_element

        items = [mock_item]
        result = write_xml(items, config)

        # Check that render_xml_element was called
        mock_item.render_xml_element.assert_called_once_with(config)

        # Check the element was included
        root = ET.fromstring(result)
        file_elem = root.find(".//file[@path='/test/mock.py']")
        assert file_elem is not None

    def test_write_xml_with_metadata_types(self, config, sample_file):
        """Test XML writing with various metadata types in compression."""
        config.enable_compression = True

        # Mock compressed segment with various metadata types
        segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="class Test:\n    pass",
            start_line=1,
            end_line=2,
            metadata={
                "string": "test",
                "integer": 42,
                "float": 3.14,
                "boolean": True,
                "complex": {"nested": "object"},  # Should be skipped
            },
        )
        config._compressed_segments = {sample_file.file_path: [segment]}

        items = [sample_file]
        result = write_xml(items, config)
        root = ET.fromstring(result)

        # Check metadata handling
        metadata_elem = root.find(".//segment/metadata")
        assert metadata_elem is not None

        # Check each metadata type
        items_found = {item.get("key"): item.text for item in metadata_elem.findall("item")}
        assert items_found["string"] == "test"
        assert items_found["integer"] == "42"
        assert items_found["float"] == "3.14"
        assert items_found["boolean"] == "True"
        assert "complex" not in items_found  # Complex types should be skipped

    def test_write_xml_without_directory_structure_in_config(self, config, sample_file):
        """Test XML writing when directory structure is disabled."""
        config.include_directory_structure = False
        items = [sample_file]
        folder_tree = "├── src/\n└── README.md"

        result = write_xml(items, config, folder_tree)
        root = ET.fromstring(result)

        # Directory structure should not be included
        tree_elem = root.find(".//directory_structure")
        assert tree_elem is None

    def test_write_xml_cdata_sections(self, config):
        """Test that special XML characters are properly encoded."""
        file_with_xml = AnnotatedFileData(
            file_path="/test/xml_content.py",
            content='xml_str = "<tag>content</tag>"',
            annotated_content='xml_str = "<tag>content</tag>"',
            language="python",
            summary="",
            tags=[],
        )

        items = [file_with_xml]
        result = write_xml(items, config)

        # Parse the XML to ensure it's valid
        root = ET.fromstring(result)

        # Find the file content
        file_elem = root.find(".//file[@path='/test/xml_content.py']")
        assert file_elem is not None

        # Content should be properly escaped (either as CDATA or entity encoding)
        # The actual content will be accessible via text attribute after parsing
        content_elem = file_elem.find(".//content")
        if content_elem is not None:
            # The special characters should be preserved when parsed
            assert "<tag>" in content_elem.text or "&lt;tag&gt;" in result
