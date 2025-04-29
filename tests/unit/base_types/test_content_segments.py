"""Unit tests for ContentSegment validation and schemas."""

import unittest

from codeconcat.base_types import (
    ContentSegment,
    ContentSegmentType,
    SecurityIssue,
    SecuritySeverity,
)


class TestContentSegments(unittest.TestCase):
    """Test cases for ContentSegment types and validation."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample segments for testing
        self.code_segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="def example():\n    return True",
            start_line=10,
            end_line=11,
            metadata={
                "importance_score": 0.8,
                "has_declaration": True,
                "declaration_names": ["example"],
            },
        )

        self.omitted_segment = ContentSegment(
            segment_type=ContentSegmentType.OMITTED,
            content="[...code omitted (10 lines, 0 issues)...]",
            start_line=20,
            end_line=30,
            metadata={
                "importance_score": 0.2,
                "original_content": "# This content was omitted\nx = 1\ny = 2\n...",
                "line_count": 10,
                "issue_count": 0,
            },
        )

    def test_segment_types(self):
        """Test ContentSegmentType enumeration values."""
        # Verify the enum values match expected string values
        self.assertEqual(ContentSegmentType.CODE.value, "code")
        self.assertEqual(ContentSegmentType.OMITTED.value, "omitted")

        # Test that the enum can be converted to/from string
        self.assertEqual(ContentSegmentType("code"), ContentSegmentType.CODE)
        self.assertEqual(ContentSegmentType("omitted"), ContentSegmentType.OMITTED)

    def test_content_segment_creation(self):
        """Test creation of ContentSegment objects."""
        # Basic validation
        self.assertEqual(self.code_segment.segment_type, ContentSegmentType.CODE)
        self.assertEqual(self.omitted_segment.segment_type, ContentSegmentType.OMITTED)

        # Check line numbers
        self.assertEqual(self.code_segment.start_line, 10)
        self.assertEqual(self.code_segment.end_line, 11)

        # Check content
        self.assertTrue(self.code_segment.content.startswith("def example()"))
        self.assertTrue(self.omitted_segment.content.startswith("[...code omitted"))

        # Check metadata
        self.assertEqual(self.code_segment.metadata["importance_score"], 0.8)
        self.assertEqual(self.omitted_segment.metadata["line_count"], 10)

    def test_segment_with_security_issues(self):
        """Test ContentSegment with security issues in metadata."""
        # Create a segment with security issues
        security_segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="password = 'secret123'",
            start_line=15,
            end_line=15,
            metadata={
                "importance_score": 0.9,
                "has_security_issues": True,
                "security_issues": [
                    SecurityIssue(
                        rule_id="hardcoded_password",
                        description="Hardcoded password detected",
                        file_path="test.py",
                        line_number=15,
                        severity=SecuritySeverity.HIGH,
                        context="password = 'secret123'",
                    )
                ],
            },
        )

        # Validate the security issue information
        self.assertTrue(security_segment.metadata["has_security_issues"])
        self.assertEqual(len(security_segment.metadata["security_issues"]), 1)

        # Check security issue details
        issue = security_segment.metadata["security_issues"][0]
        self.assertEqual(issue.rule_id, "hardcoded_password")
        self.assertEqual(issue.severity, SecuritySeverity.HIGH)

    def test_segment_serialization(self):
        """Test that ContentSegment can be serialized to dict."""
        # Convert to dict
        code_segment_dict = {
            "segment_type": self.code_segment.segment_type.value,
            "content": self.code_segment.content,
            "start_line": self.code_segment.start_line,
            "end_line": self.code_segment.end_line,
            "metadata": self.code_segment.metadata,
        }

        # Verify fields
        self.assertEqual(code_segment_dict["segment_type"], "code")
        self.assertEqual(code_segment_dict["start_line"], 10)
        self.assertEqual(code_segment_dict["end_line"], 11)

        # Check metadata
        self.assertEqual(code_segment_dict["metadata"]["importance_score"], 0.8)
        self.assertTrue(code_segment_dict["metadata"]["has_declaration"])

    def test_segment_with_empty_metadata(self):
        """Test ContentSegment with no metadata."""
        # Create segment with empty metadata
        empty_meta_segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="# Empty metadata test",
            start_line=1,
            end_line=1,
            metadata={},
        )

        # Verify empty metadata doesn't cause issues
        self.assertEqual(empty_meta_segment.metadata, {})

        # Should be serializable with empty metadata
        segment_dict = {
            "segment_type": empty_meta_segment.segment_type.value,
            "content": empty_meta_segment.content,
            "start_line": empty_meta_segment.start_line,
            "end_line": empty_meta_segment.end_line,
            "metadata": empty_meta_segment.metadata,
        }

        self.assertEqual(segment_dict["metadata"], {})

    def test_content_segment_equality(self):
        """Test equality comparison of ContentSegment objects."""
        # Create identical segment
        identical_segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="def example():\n    return True",
            start_line=10,
            end_line=11,
            metadata={
                "importance_score": 0.8,
                "has_declaration": True,
                "declaration_names": ["example"],
            },
        )

        # Create different segment
        different_segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="def example():\n    return True",
            start_line=12,  # Different line number
            end_line=13,
            metadata={
                "importance_score": 0.8,
                "has_declaration": True,
                "declaration_names": ["example"],
            },
        )

        # Test equality
        self.assertEqual(self.code_segment, identical_segment)
        self.assertNotEqual(self.code_segment, different_segment)
        self.assertNotEqual(self.code_segment, self.omitted_segment)


if __name__ == "__main__":
    unittest.main()
