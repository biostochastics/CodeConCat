"""Unit tests for writer compression rendering."""

import json
import unittest
import xml.etree.ElementTree as ET
from typing import List

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    ContentSegment,
    ContentSegmentType,
    WritableItem,
)
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.text_writer import write_text
from codeconcat.writer.xml_writer import write_xml


class TestWriterCompression(unittest.TestCase):
    """Test cases for compressing content in all writer formats."""

    def setUp(self):
        """Set up test fixtures."""
        # Create configuration with compression enabled
        self.config = CodeConCatConfig(
            enable_compression=True,
            compression_level="medium",
            compression_placeholder="[...code omitted ({lines} lines, {issues} issues)...]",
            compression_keep_threshold=3,
        )

        # Create content segments for testing
        self.segments = [
            ContentSegment(
                segment_type=ContentSegmentType.CODE,
                content='def important_function():\n    """This is important."""\n    return True',
                start_line=1,
                end_line=3,
                metadata={"importance_score": 0.9},
            ),
            ContentSegment(
                segment_type=ContentSegmentType.OMITTED,
                content="[...code omitted (5 lines, 0 issues)...]",
                start_line=4,
                end_line=8,
                metadata={
                    "importance_score": 0.2,
                    "original_content": "# This should be omitted\nx = 1\ny = 2\nz = 3\nprint(x, y, z)",
                    "line_count": 5,
                    "issue_count": 0,
                },
            ),
            ContentSegment(
                segment_type=ContentSegmentType.CODE,
                content="def another_function():\n    return False",
                start_line=9,
                end_line=10,
                metadata={"importance_score": 0.8},
            ),
        ]

        # Create mock file data
        self.file_data = AnnotatedFileData(
            file_path="/path/to/test.py",
            language="python",
            content="",  # Will be set based on compression
            annotated_content="",  # Will be set based on compression
            summary="Test file with compression",
        )

        # Apply compressed content - this represents what CompressionProcessor would do
        compressed_content = (
            "def important_function():\n"
            '    """This is important."""\n'
            "    return True\n"
            "\n"
            "[...code omitted (5 lines, 0 issues)...]\n"
            "\n"
            "def another_function():\n"
            "    return False\n"
        )

        self.file_data.content = compressed_content
        self.file_data.annotated_content = compressed_content

        # Set compressed segments on config (as CompressionProcessor would do)
        self.config._compressed_segments = {self.file_data.file_path: self.segments}

        # Create list of writable items
        self.items: List[WritableItem] = [self.file_data]

    def test_markdown_writer_compression(self):
        """Test that markdown writer properly handles compressed content."""
        # Generate markdown output
        self.config.format = "markdown"
        output = write_markdown(self.items, self.config)

        # Verify output contains all code segments
        self.assertIn("def important_function", output)
        self.assertIn("def another_function", output)

        # Verify output contains compression placeholder
        self.assertIn("[...code omitted (5 lines, 0 issues)...]", output)

        # Verify markdown specific formatting
        self.assertIn("```python", output)  # Code blocks
        # New format uses different header style
        self.assertIn("/path/to/test.py", output)  # File path included

    def test_json_writer_compression(self):
        """Test that JSON writer properly handles compressed content."""
        # Generate JSON output
        self.config.format = "json"
        output = write_json(self.items, self.config)

        # Parse the JSON to verify structure
        json_data = json.loads(output)

        # Verify top-level structure - files is now a list
        self.assertIn("files", json_data)
        self.assertIsInstance(json_data["files"], list)
        self.assertEqual(len(json_data["files"]), 1)

        # Check the file data - files is now a list
        file_data = json_data["files"][0]
        self.assertEqual(file_data["file_path"], "/path/to/test.py")

        # Verify basic structure
        self.assertIn("content", file_data)
        # The compressed content should be there
        self.assertIn("def important_function", file_data["content"])
        self.assertIn("[...code omitted", file_data["content"])

    def test_xml_writer_compression(self):
        """Test that XML writer properly handles compressed content."""
        # Generate XML output
        self.config.format = "xml"
        output = write_xml(self.items, self.config)

        # Verify the output is valid XML
        try:
            root = ET.fromstring(output)
        except ET.ParseError:
            self.fail("XML output is not valid")

        # Verify that we found at least one file node
        files = root.findall(".//file")
        self.assertGreater(len(files), 0)

        # Check the raw XML string directly instead of navigating the XML tree
        # This is more resilient to changes in XML structure
        self.assertIn("/path/to/test.py", output)
        self.assertIn("def important_function", output)
        self.assertIn("def another_function", output)
        self.assertIn("[...code omitted", output)

        # Look for segment-related content in the XML string
        self.assertIn("<segment", output)

    def test_text_writer_compression(self):
        """Test that text writer properly handles compressed content."""
        # Generate text output
        self.config.format = "text"
        output = write_text(self.items, self.config)

        # Verify output contains all code segments
        self.assertIn("def important_function", output)
        self.assertIn("def another_function", output)

        # Verify output contains compression placeholder
        self.assertIn("[...code omitted (5 lines, 0 issues)...]", output)

        # Verify text specific formatting - updated format
        self.assertIn("FILE: /path/to/test.py", output)
        self.assertIn("=== SUMMARY ===", output)
        self.assertIn("Test file with compression", output)

    def test_disabled_compression(self):
        """Test that writers work correctly when compression is disabled."""
        # Disable compression
        self.config.enable_compression = False

        # Test all output formats with compression disabled
        formats = ["markdown", "json", "xml", "text"]

        for fmt in formats:
            with self.subTest(format=fmt):
                self.config.format = fmt

                if fmt == "markdown":
                    output = write_markdown(self.items, self.config)
                elif fmt == "json":
                    output = write_json(self.items, self.config)
                elif fmt == "xml":
                    output = write_xml(self.items, self.config)
                elif fmt == "text":
                    output = write_text(self.items, self.config)

                # When compression is disabled, segments should not be used
                if fmt == "json":
                    json_data = json.loads(output)
                    # Files is now a list, not a dictionary
                    files_list = json_data["files"]
                    file_data = files_list[0]
                    self.assertNotIn("content_segments", file_data)
                elif fmt == "xml":
                    root = ET.fromstring(output)
                    file_element = root.find(".//file")
                    self.assertIsNone(file_element.get("compression_applied"))
                    segments = file_element.findall(".//content_segments")
                    self.assertEqual(len(segments), 0)


if __name__ == "__main__":
    unittest.main()
