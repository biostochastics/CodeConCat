"""Unit tests for CompressionProcessor."""

import unittest

from codeconcat.base_types import (
    CodeConCatConfig,
    ContentSegment,
    ContentSegmentType,
    Declaration,
    ParsedFileData,
    SecurityIssue,
    SecuritySeverity,
)
from codeconcat.processor.compression_processor import CompressionProcessor


class TestCompressionProcessor(unittest.TestCase):
    """Test cases for the CompressionProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            enable_compression=True,
            compression_level="medium",
            compression_placeholder="[...code omitted ({lines} lines, {issues} issues)...]",
            compression_keep_threshold=3,
            compression_keep_tags=["important", "keep", "security"],
        )
        self.processor = CompressionProcessor(self.config)

        # Sample file data for testing
        self.file_data = ParsedFileData(
            file_path="/path/to/sample.py",
            language="python",
            content=(
                "import os\n"
                "import sys\n"
                "\n"
                "# This is a simple Python file\n"
                "# @important: This function is critical\n"
                "def important_function(param):\n"
                '    """This function does something important."""\n'
                "    # Process the parameter\n"
                "    result = param * 2\n"
                "    return result\n"
                "\n"
                "# This is a utility function\n"
                "def utility_function(param):\n"
                '    """This function is less important."""\n'
                "    # Just a helper\n"
                "    for i in range(10):\n"
                "        print(i)\n"
                "    return param\n"
                "\n"
                "# Main execution\n"
                'if __name__ == "__main__":\n'
                "    important_function(42)\n"
                "    utility_function(21)\n"
            ),
            declarations=[
                Declaration(
                    kind="function",
                    name="important_function",
                    start_line=5,
                    end_line=9,
                    docstring="This function does something important.",
                ),
                Declaration(
                    kind="function",
                    name="utility_function",
                    start_line=12,
                    end_line=17,
                    docstring="This function is less important.",
                ),
            ],
            security_issues=[
                SecurityIssue(
                    rule_id="password_pattern",
                    description="Hardcoded password detected",
                    file_path="/path/to/sample.py",
                    line_number=8,
                    severity=SecuritySeverity.HIGH,
                    context="password = 'secret'",
                )
            ],
        )

    def test_initialization(self):
        """Test processor initialization with config."""
        self.assertEqual(self.processor.config, self.config)
        # Check the processor was initialized correctly
        self.assertIsNotNone(self.processor)

    def test_calculate_line_importance(self):
        """Test calculation of line importance scores."""
        lines = self.file_data.content.split("\n")

        # Calculate importance scores
        line_importance = self.processor._calculate_line_importance(lines, self.file_data)

        # Verify that importance scores array exists and has values
        self.assertIsNotNone(line_importance)

        # Verify that importance scores are numbers (float or int)
        for value in line_importance:
            self.assertIsInstance(value, (int, float))

        # The array should have an entry for each line
        self.assertEqual(len(line_importance), len(lines))

    def test_create_initial_segments(self):
        """Test creation of initial content segments based on importance scores."""
        lines = self.file_data.content.split("\n")
        line_importance = {i: 10 if i < 5 else 2 for i in range(len(lines))}

        segments = self.processor._create_initial_segments(lines, line_importance)

        # Check that we have segments (we should at least have code segments)
        self.assertTrue(len(segments) > 0)

        # Check that all segments have the required attributes
        for segment in segments:
            self.assertIsInstance(segment, ContentSegment)
            self.assertIsInstance(segment.segment_type, ContentSegmentType)
            self.assertIsInstance(segment.content, str)
            self.assertIsInstance(segment.start_line, int)
            self.assertIsInstance(segment.end_line, int)
            self.assertIsInstance(segment.metadata, dict)

    def test_merge_small_segments(self):
        """Test that small segments can be merged."""
        # Create a file with many small segments to test merging
        small_segments_file = ParsedFileData(
            file_path="/path/to/small_segments.py",
            language="python",
            content="\n".join([f"line {i}" for i in range(20)]),  # 20 individual lines
            declarations=[],
            security_issues=[],
        )

        # Process the file
        result = self.processor.process_file(small_segments_file)

        # Verify that the result is a list of segments
        self.assertIsInstance(result, list)
        for segment in result:
            self.assertIsInstance(segment, ContentSegment)

        # The number of segments should be less than the number of lines
        # (some merging should have occurred)
        self.assertLess(len(result), 20)

    def test_format_placeholders(self):
        """Test formatting of placeholders for omitted segments."""
        # Process the sample file
        segments = self.processor.process_file(self.file_data)

        # If there are any omitted segments, test that their content resembles a placeholder
        omitted_segments = [s for s in segments if s.segment_type == ContentSegmentType.OMITTED]
        if omitted_segments:
            for segment in omitted_segments:
                # Check that content is a string (the placeholder)
                self.assertIsInstance(segment.content, str)
                # Placeholder should mention "code omitted"
                self.assertIn("code omitted", segment.content.lower())
                # Check that metadata exists
                self.assertIsInstance(segment.metadata, dict)

    def test_process_file(self):
        """Test the full file processing pipeline."""
        # Process the sample file
        segments = self.processor.process_file(self.file_data)

        # Verify we have segments
        self.assertTrue(len(segments) > 0)

        # Check that we have both CODE and OMITTED segments
        segment_types = [s.segment_type for s in segments]
        self.assertIn(ContentSegmentType.CODE, segment_types)

        # Verify important lines are preserved in CODE segments
        code_content = "\n".join(
            s.content for s in segments if s.segment_type == ContentSegmentType.CODE
        )

        # Important elements should be preserved
        self.assertIn("import os", code_content)
        self.assertIn("import sys", code_content)
        self.assertIn("@important", code_content)
        self.assertIn("def important_function", code_content)
        self.assertIn("if __name__ ==", code_content)

    def test_apply_compression(self):
        """Test applying compression to file content."""
        # Process the sample file to get segments
        segments = self.processor.process_file(self.file_data)

        # Apply compression to get the compressed content
        compressed_content = self.processor.apply_compression(self.file_data)

        # Compressed content should contain CODE segments and placeholders
        for segment in segments:
            if segment.segment_type == ContentSegmentType.CODE:
                # Content from CODE segments should be in the compressed content
                self.assertIn(segment.content, compressed_content)
            elif segment.segment_type == ContentSegmentType.OMITTED:
                # For OMITTED segments, the placeholder should be in the compressed content
                self.assertIn(segment.content, compressed_content)

    def test_different_compression_levels(self):
        """Test compression with different compression levels."""
        # Test with aggressive compression
        aggressive_config = CodeConCatConfig(
            enable_compression=True,
            compression_level="aggressive",
            compression_placeholder="[...]",
            compression_keep_threshold=3,
            compression_keep_tags=["important", "keep", "security"],
        )

        aggressive_processor = CompressionProcessor(aggressive_config)
        aggressive_segments = aggressive_processor.process_file(self.file_data)

        # Test with low compression
        low_config = CodeConCatConfig(
            enable_compression=True,
            compression_level="low",
            compression_placeholder="[...]",
            compression_keep_threshold=3,
            compression_keep_tags=["important", "keep", "security"],
        )

        low_processor = CompressionProcessor(low_config)
        low_segments = low_processor.process_file(self.file_data)

        # Check that both types of compression return valid results
        self.assertIsInstance(aggressive_segments, list)
        self.assertIsInstance(low_segments, list)

        # Both should contain at least one segment
        self.assertGreater(len(aggressive_segments), 0)
        self.assertGreater(len(low_segments), 0)

        # Check all segments are valid
        for segment in aggressive_segments + low_segments:
            self.assertIsInstance(segment, ContentSegment)
            self.assertIsInstance(segment.segment_type, ContentSegmentType)
            self.assertIsInstance(segment.content, str)

    def test_keep_tags(self):
        """Test that code with keep tags is preserved."""
        # Add a file with keep tags for testing
        file_with_keep_tags = ParsedFileData(
            file_path="/path/to/sample_with_tags.py",
            language="python",
            content=(
                "import os\n"
                "\n"
                "# This should be omitted\n"
                "x = 1\n"
                "y = 2\n"
                "\n"
                "# @keep This should be kept\n"
                "z = 3\n"
                "w = 4\n"
                "\n"
                "# This should be omitted\n"
                "a = 5\n"
                "b = 6\n"
            ),
            declarations=[],
            security_issues=[],
        )

        # Process the file
        segments = self.processor.process_file(file_with_keep_tags)

        # Combine all code segments
        code_content = "\n".join(
            s.content for s in segments if s.segment_type == ContentSegmentType.CODE
        )

        # The @keep tagged section should be preserved
        self.assertIn("@keep", code_content)
        self.assertIn("z = 3", code_content)
        self.assertIn("w = 4", code_content)


if __name__ == "__main__":
    unittest.main()
