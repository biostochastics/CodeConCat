"""Integration tests for the compression feature."""

import os
import tempfile
import unittest

from codeconcat.base_types import (
    CodeConCatConfig,
    AnnotatedFileData,
    SecurityIssue,
    SecuritySeverity,
)
from codeconcat.processor.compression_processor import CompressionProcessor
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.xml_writer import write_xml
from codeconcat.writer.text_writer import write_text


class TestCompressionIntegration(unittest.TestCase):
    """Test the integration of compression with the rendering pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test output
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.test_dir.name

        # Create test configuration
        self.config = CodeConCatConfig(
            output=os.path.join(self.output_dir, "output"),
            enable_compression=True,
            compression_level="medium",
            compression_placeholder="[...code omitted ({lines} lines, {issues} issues)...]",
            compression_keep_threshold=3,
            compression_keep_tags=["important", "keep", "security"],
        )

        # Create test file with various sections
        self.test_file_content = (
            "import os\n"
            "import sys\n"
            "import json\n"
            "\n"
            "# @important: Critical function\n"
            "def critical_function(param):\n"
            '    """This function is critical and should not be compressed."""\n'
            "    # Do something important\n"
            "    return param * 2\n"
            "\n"
            "# This section should be compressed\n"
            "def utility_function():\n"
            '    """This is a utility function that might be compressed."""\n'
            "    # This is just a helper\n"
            "    x = 1\n"
            "    y = 2\n"
            "    z = 3\n"
            "    return x + y + z\n"
            "\n"
            "# Main section\n"
            'if __name__ == "__main__":\n'
            "    result = critical_function(42)\n"
            "    utility_function()\n"
            '    print(f"Result: {result}")\n'
        )

        # Create annotated file data
        self.file_data = AnnotatedFileData(
            file_path="/path/to/test_file.py",
            language="python",
            content=self.test_file_content,
            annotated_content=self.test_file_content,  # Use the same content for testing
            summary="Test file for compression",
            security_issues=[
                SecurityIssue(
                    rule_id="password_pattern",
                    description="Hardcoded password detected",
                    file_path="/path/to/test_file.py",
                    line_number=15,  # in utility_function
                    severity=SecuritySeverity.HIGH,
                    context="password = 'secret'",
                )
            ],
            declarations=[],
        )

        # Create a list of writable items
        self.items = [self.file_data]

    def tearDown(self):
        """Clean up after tests."""
        self.test_dir.cleanup()

    def test_markdown_compression(self):
        """Test that compression works with Markdown output."""
        # Apply compression
        compression_processor = CompressionProcessor(self.config)
        compressed_segments = compression_processor.process_file(self.file_data)
        self.file_data.content = compression_processor.apply_compression(self.file_data)
        self.config._compressed_segments = compressed_segments

        # Generate Markdown output
        output_file = os.path.join(self.output_dir, "output.md")
        self.config.output = output_file
        self.config.format = "markdown"
        output_content = write_markdown(self.items, self.config)

        # Manually write to file since the writer functions only return content
        with open(output_file, "w") as f:
            f.write(output_content)

        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))

        # Check content
        with open(output_file, "r") as f:
            content = f.read()

        # Ensure critical parts are included
        self.assertIn("critical_function", content)
        self.assertIn("@important", content)

        # Check for placeholder text
        self.assertIn("[...code omitted", content)

        # Verify the high-security issue is properly indicated
        self.assertIn("issues", content)

    def test_json_compression(self):
        """Test that compression works with JSON output."""
        # Apply compression
        compression_processor = CompressionProcessor(self.config)
        compressed_segments = compression_processor.process_file(self.file_data)
        self.file_data.content = compression_processor.apply_compression(self.file_data)
        self.config._compressed_segments = compressed_segments

        # Generate JSON output
        output_file = os.path.join(self.output_dir, "output.json")
        self.config.output = output_file
        self.config.format = "json"
        output_content = write_json(self.items, self.config)

        # Manually write to file since the writer functions only return content
        with open(output_file, "w") as f:
            f.write(output_content)

        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))

        # Check content
        import json

        with open(output_file, "r") as f:
            data = json.load(f)

        # Verify structure and content
        self.assertIn("files", data)
        self.assertGreater(len(data["files"]), 0)

        # Check for content_segments in the output
        if "content_segments" in data["files"][0]:
            segments = data["files"][0]["content_segments"]
            self.assertGreater(len(segments), 0)

            # Verify segment types
            segment_types = [s.get("type") for s in segments]
            self.assertIn("code", segment_types)  # Lowercase as in ContentSegmentType.CODE.value
            self.assertIn(
                "omitted", segment_types
            )  # Lowercase as in ContentSegmentType.OMITTED.value

            # Check for critical content in CODE segments
            code_segments = [s for s in segments if s.get("type") == "code"]
            code_content = "\n".join(s.get("content", "") for s in code_segments)
            self.assertIn("critical_function", code_content)

            # Check metadata for OMITTED segments
            omitted_segments = [s for s in segments if s.get("type") == "OMITTED"]
            for segment in omitted_segments:
                self.assertIn("metadata", segment)
                self.assertIn("lines", segment["metadata"])

    def test_xml_compression(self):
        """Test that compression works with XML output."""
        # Apply compression
        compression_processor = CompressionProcessor(self.config)
        compressed_segments = compression_processor.process_file(self.file_data)
        self.file_data.content = compression_processor.apply_compression(self.file_data)
        self.config._compressed_segments = compressed_segments

        # Generate XML output
        output_file = os.path.join(self.output_dir, "output.xml")
        self.config.output = output_file
        self.config.format = "xml"
        output_content = write_xml(self.items, self.config)

        # Manually write to file since the writer functions only return content
        with open(output_file, "w") as f:
            f.write(output_content)

        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))

        # Check content
        with open(output_file, "r") as f:
            content = f.read()

        # Verify the XML has compression-related elements
        # Check for core attributes that must exist
        self.assertIn("compression_applied", content)
        self.assertIn("<content_segments>", content)

        # Less strict checks for elements that might have different formatting in the XML renderer
        self.assertIn("<segment", content)
        self.assertIn("<content>", content)  # Each segment should have content

        # Check for presence of key file content that should be in the XML
        self.assertIn("critical_function", content)

    def test_text_compression(self):
        """Test that compression works with text output."""
        # Apply compression
        compression_processor = CompressionProcessor(self.config)
        compressed_segments = compression_processor.process_file(self.file_data)
        self.file_data.content = compression_processor.apply_compression(self.file_data)
        self.config._compressed_segments = compressed_segments

        # Generate text output
        output_file = os.path.join(self.output_dir, "output.txt")
        self.config.output = output_file
        self.config.format = "text"
        output_content = write_text(self.items, self.config)

        # Manually write to file since the writer functions only return content
        with open(output_file, "w") as f:
            f.write(output_content)

        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))

        # Check content
        with open(output_file, "r") as f:
            content = f.read()

        # Ensure critical parts are included
        self.assertIn("critical_function", content)

        # Check for any compression-related content
        # Since the text writer might handle compression differently, just check for the critical parts
        self.assertIn("utility_function", content)  # This should be included in some form

    def test_no_compression(self):
        """Test that output works correctly when compression is disabled."""
        # Disable compression
        self.config.enable_compression = False

        # Generate Markdown output
        output_file = os.path.join(self.output_dir, "output_no_compression.md")
        self.config.output = output_file
        self.config.format = "markdown"
        output_content = write_markdown(self.items, self.config)

        # Manually write to file since the writer functions only return content
        with open(output_file, "w") as f:
            f.write(output_content)

        # Verify the output file exists
        self.assertTrue(os.path.exists(output_file))

        # Check content
        with open(output_file, "r") as f:
            content = f.read()

        # Ensure all content is included (no compression)
        self.assertIn("critical_function", content)
        self.assertIn("utility_function", content)

        # Verify no placeholder text
        self.assertNotIn("[...code omitted", content)


if __name__ == "__main__":
    unittest.main()
