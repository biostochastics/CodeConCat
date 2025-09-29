"""Test AI summary generation across all output formats."""

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pytest

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, Declaration
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.text_writer import write_text
from codeconcat.writer.xml_writer import write_xml


@pytest.fixture
def config_with_ai():
    """Create config with AI summary enabled."""
    return CodeConCatConfig(
        project_path=".",
        format="markdown",
        enable_ai_summary=True,
        ai_provider="anthropic",
        ai_api_key="test_key",
        ai_model="claude-3-haiku-20240307",
        include_file_summary=True,
        include_directory_structure=True,
        include_repo_overview=True,
    )


@pytest.fixture
def sample_file_with_ai_summary():
    """Create a sample file with AI summary."""
    return AnnotatedFileData(
        file_path="test_module.py",
        language="python",
        content='''def calculate_total(items):
    """Calculate total price of items."""
    return sum(item.price for item in items)

def validate_order(order):
    """Validate order details."""
    if not order.items:
        raise ValueError("Order must have items")
    return True
''',
        annotated_content='''## File: test_module.py
### Functions
- calculate_total
- validate_order
```python
def calculate_total(items):
    """Calculate total price of items."""
    return sum(item.price for item in items)

def validate_order(order):
    """Validate order details."""
    if not order.items:
        raise ValueError("Order must have items")
    return True
```
''',
        summary="Module for order processing calculations",
        ai_summary="This module provides essential e-commerce order processing functionality. The calculate_total function efficiently computes the aggregate price of items using a generator expression, while validate_order ensures order integrity by checking for non-empty item lists, raising informative errors for invalid states.",
        imports=["from typing import List"],
        declarations=[
            Declaration(
                kind="function",
                name="calculate_total",
                start_line=1,
                end_line=3,
                modifiers=set(),
                docstring="Calculate total price of items.",
                children=[],
            ),
            Declaration(
                kind="function",
                name="validate_order",
                start_line=5,
                end_line=9,
                modifiers=set(),
                docstring="Validate order details.",
                children=[],
            ),
        ],
    )


@pytest.fixture
def sample_file_without_ai_summary():
    """Create a sample file without AI summary."""
    return AnnotatedFileData(
        file_path="utils.py",
        language="python",
        content='''def format_date(date):
    """Format date to string."""
    return date.strftime("%Y-%m-%d")
''',
        annotated_content='''## File: utils.py
### Functions
- format_date
```python
def format_date(date):
    """Format date to string."""
    return date.strftime("%Y-%m-%d")
```
''',
        summary="Utility functions for date formatting",
        ai_summary=None,  # No AI summary
        imports=[],
        declarations=[
            Declaration(
                kind="function",
                name="format_date",
                start_line=1,
                end_line=3,
                modifiers=set(),
                docstring="Format date to string.",
                children=[],
            ),
        ],
    )


class TestMarkdownFormatWithAISummary:
    """Test AI summary generation in Markdown format."""

    def test_markdown_includes_ai_summary(self, config_with_ai, sample_file_with_ai_summary):
        """Test that Markdown output includes AI summary when present."""
        config_with_ai.format = "markdown"
        items = [sample_file_with_ai_summary]

        output = write_markdown(items, config_with_ai)

        # Check that AI summary is included
        assert "AI Summary" in output
        assert sample_file_with_ai_summary.ai_summary in output
        assert "essential e-commerce order processing functionality" in output

    def test_markdown_without_ai_summary(self, config_with_ai, sample_file_without_ai_summary):
        """Test that Markdown output handles files without AI summary."""
        config_with_ai.format = "markdown"
        items = [sample_file_without_ai_summary]

        output = write_markdown(items, config_with_ai)

        # Check that regular summary is included but no AI summary
        assert sample_file_without_ai_summary.summary in output
        assert "AI Summary" not in output

    def test_markdown_mixed_files(
        self, config_with_ai, sample_file_with_ai_summary, sample_file_without_ai_summary
    ):
        """Test Markdown with both AI-summarized and regular files."""
        config_with_ai.format = "markdown"
        items = [sample_file_with_ai_summary, sample_file_without_ai_summary]

        output = write_markdown(items, config_with_ai)

        # Check both files are present
        assert "test_module.py" in output
        assert "utils.py" in output

        # Check AI summary only for the appropriate file
        assert sample_file_with_ai_summary.ai_summary in output
        assert "Utility functions for date formatting" in output


class TestJSONFormatWithAISummary:
    """Test AI summary generation in JSON format."""

    def test_json_includes_ai_summary(self, config_with_ai, sample_file_with_ai_summary):
        """Test that JSON output includes AI summary when present."""
        config_with_ai.format = "json"
        items = [sample_file_with_ai_summary]

        output = write_json(items, config_with_ai)
        json_data = json.loads(output)

        # Check that AI summary is in the JSON structure
        assert "files" in json_data
        assert len(json_data["files"]) == 1
        file_data = json_data["files"][0]

        assert "ai_summary" in file_data
        assert file_data["ai_summary"] == sample_file_with_ai_summary.ai_summary
        assert "essential e-commerce order processing functionality" in file_data["ai_summary"]

    def test_json_without_ai_summary(self, config_with_ai, sample_file_without_ai_summary):
        """Test that JSON output handles files without AI summary."""
        config_with_ai.format = "json"
        items = [sample_file_without_ai_summary]

        output = write_json(items, config_with_ai)
        json_data = json.loads(output)

        file_data = json_data["files"][0]

        # Check that regular summary is included but no AI summary
        assert "summary" in file_data
        assert file_data["summary"] == sample_file_without_ai_summary.summary
        assert "ai_summary" not in file_data

    def test_json_preserves_all_metadata(self, config_with_ai, sample_file_with_ai_summary):
        """Test that JSON preserves all metadata including AI summary."""
        config_with_ai.format = "json"
        items = [sample_file_with_ai_summary]

        output = write_json(items, config_with_ai)
        json_data = json.loads(output)

        file_data = json_data["files"][0]

        # Check all expected fields are present
        assert file_data["file_path"] == "test_module.py"
        assert file_data["language"] == "python"
        assert "summary" in file_data
        assert "ai_summary" in file_data
        assert "declarations" in file_data
        assert len(file_data["declarations"]) == 2


class TestXMLFormatWithAISummary:
    """Test AI summary generation in XML format."""

    def test_xml_includes_ai_summary(self, config_with_ai, sample_file_with_ai_summary):
        """Test that XML output includes AI summary when present."""
        config_with_ai.format = "xml"
        items = [sample_file_with_ai_summary]

        output = write_xml(items, config_with_ai)
        root = ET.fromstring(output)

        # Find the file element - it's in file_entry/file_metadata structure
        file_entries = root.findall(".//file_entry")
        file_elem = None
        for entry in file_entries:
            path_elem = entry.find(".//file_metadata/path")
            if path_elem is not None and path_elem.text == "test_module.py":
                file_elem = entry
                break

        assert file_elem is not None, "Could not find file entry for test_module.py"

        # Check for AI summary element in file_metadata
        ai_summary_elem = file_elem.find(".//file_metadata/ai_summary")
        assert ai_summary_elem is not None
        assert ai_summary_elem.text == sample_file_with_ai_summary.ai_summary
        assert "essential e-commerce order processing functionality" in ai_summary_elem.text

    def test_xml_without_ai_summary(self, config_with_ai, sample_file_without_ai_summary):
        """Test that XML output handles files without AI summary."""
        config_with_ai.format = "xml"
        items = [sample_file_without_ai_summary]

        output = write_xml(items, config_with_ai)
        root = ET.fromstring(output)

        # Find the file element - it's in file_entry/file_metadata structure
        file_entries = root.findall(".//file_entry")
        file_elem = None
        for entry in file_entries:
            path_elem = entry.find(".//file_metadata/path")
            if path_elem is not None and path_elem.text == "utils.py":
                file_elem = entry
                break

        assert file_elem is not None, "Could not find file entry for utils.py"

        # Check that regular summary is included but no AI summary
        summary_elem = file_elem.find(".//file_metadata/summary")
        assert summary_elem is not None
        assert summary_elem.text == sample_file_without_ai_summary.summary

        ai_summary_elem = file_elem.find(".//file_metadata/ai_summary")
        assert ai_summary_elem is None

    def test_xml_structure_with_ai_summary(self, config_with_ai, sample_file_with_ai_summary):
        """Test that XML structure is valid with AI summary."""
        config_with_ai.format = "xml"
        items = [sample_file_with_ai_summary]

        output = write_xml(items, config_with_ai)

        # Verify it's valid XML
        try:
            root = ET.fromstring(output)
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML generated: {e}")

        # Check structure
        assert root.tag == "codebase_analysis"
        content_elem = root.find("codebase_content")
        assert content_elem is not None
        files_elem = content_elem.find("files")
        assert files_elem is not None
        assert len(files_elem.findall("file_entry")) == 1


class TestTextFormatWithAISummary:
    """Test AI summary handling in Text format."""

    def test_text_format_basic_output(self, config_with_ai, sample_file_with_ai_summary):
        """Test that text format generates valid output with AI-summarized content."""
        config_with_ai.format = "text"
        items = [sample_file_with_ai_summary]

        output = write_text(items, config_with_ai)

        # Check basic structure
        assert "CODECONCAT OUTPUT" in output
        assert "test_module.py" in output
        assert "def calculate_total" in output
        assert "def validate_order" in output

    def test_text_format_with_multiple_files(
        self, config_with_ai, sample_file_with_ai_summary, sample_file_without_ai_summary
    ):
        """Test text format with mixed AI-summarized and regular files."""
        config_with_ai.format = "text"
        items = [sample_file_with_ai_summary, sample_file_without_ai_summary]

        output = write_text(items, config_with_ai)

        # Check both files are present
        assert "test_module.py" in output
        assert "utils.py" in output
        assert "Files: 2" in output

    def test_text_format_statistics(self, config_with_ai, sample_file_with_ai_summary):
        """Test that text format includes proper statistics."""
        config_with_ai.format = "text"
        items = [sample_file_with_ai_summary]

        output = write_text(items, config_with_ai)

        # Check statistics section
        assert "SUMMARY" in output
        assert "Files: 1" in output
        assert "Languages: 1" in output


class TestAISummaryPersistence:
    """Test that AI summaries are properly saved to files."""

    def test_markdown_file_save(self, config_with_ai, sample_file_with_ai_summary):
        """Test saving Markdown with AI summary to file."""
        config_with_ai.format = "markdown"
        items = [sample_file_with_ai_summary]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output = write_markdown(items, config_with_ai)
            f.write(output)
            temp_path = f.name

        # Read back and verify
        saved_content = Path(temp_path).read_text()
        assert "AI Summary" in saved_content
        assert sample_file_with_ai_summary.ai_summary in saved_content

        # Cleanup
        Path(temp_path).unlink()

    def test_json_file_save(self, config_with_ai, sample_file_with_ai_summary):
        """Test saving JSON with AI summary to file."""
        config_with_ai.format = "json"
        items = [sample_file_with_ai_summary]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output = write_json(items, config_with_ai)
            f.write(output)
            temp_path = f.name

        # Read back and verify
        saved_content = Path(temp_path).read_text()
        saved_json = json.loads(saved_content)

        assert "files" in saved_json
        assert "ai_summary" in saved_json["files"][0]
        assert saved_json["files"][0]["ai_summary"] == sample_file_with_ai_summary.ai_summary

        # Cleanup
        Path(temp_path).unlink()

    def test_xml_file_save(self, config_with_ai, sample_file_with_ai_summary):
        """Test saving XML with AI summary to file."""
        config_with_ai.format = "xml"
        items = [sample_file_with_ai_summary]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output = write_xml(items, config_with_ai)
            f.write(output)
            temp_path = f.name

        # Read back and verify
        saved_content = Path(temp_path).read_text()
        root = ET.fromstring(saved_content)

        # Find the file element - it's in file_entry/file_metadata structure
        file_entries = root.findall(".//file_entry")
        file_elem = None
        for entry in file_entries:
            path_elem = entry.find(".//file_metadata/path")
            if path_elem is not None and path_elem.text == "test_module.py":
                file_elem = entry
                break

        assert file_elem is not None, "Could not find file entry for test_module.py"
        ai_summary_elem = file_elem.find(".//file_metadata/ai_summary")
        assert ai_summary_elem is not None
        assert ai_summary_elem.text == sample_file_with_ai_summary.ai_summary

        # Cleanup
        Path(temp_path).unlink()


class TestAISummaryErrorHandling:
    """Test error handling when AI provider is unavailable."""

    @patch("codeconcat.processor.summarization_processor.get_ai_provider")
    def test_graceful_degradation_no_provider(
        self, mock_get_provider, config_with_ai, sample_file_without_ai_summary
    ):
        """Test that output still works when AI provider fails to initialize."""
        # Simulate provider initialization failure
        mock_get_provider.side_effect = Exception("API key invalid")

        # Files should still be processed without AI summaries
        for format_type in ["markdown", "json", "xml", "text"]:
            config_with_ai.format = format_type
            items = [sample_file_without_ai_summary]

            # Should not raise exception
            if format_type == "markdown":
                output = write_markdown(items, config_with_ai)
            elif format_type == "json":
                output = write_json(items, config_with_ai)
            elif format_type == "xml":
                output = write_xml(items, config_with_ai)
            else:  # text
                output = write_text(items, config_with_ai)

            assert output  # Output should be generated
            assert "utils.py" in output  # File should be included

    def test_mixed_ai_summaries(
        self, config_with_ai, sample_file_with_ai_summary, sample_file_without_ai_summary
    ):
        """Test handling mixed files with and without AI summaries."""
        # Test all formats handle mixed content gracefully
        for format_type in ["markdown", "json", "xml", "text"]:
            config_with_ai.format = format_type
            items = [sample_file_with_ai_summary, sample_file_without_ai_summary]

            # Generate output
            if format_type == "markdown":
                output = write_markdown(items, config_with_ai)
            elif format_type == "json":
                output = write_json(items, config_with_ai)
            elif format_type == "xml":
                output = write_xml(items, config_with_ai)
            else:  # text
                output = write_text(items, config_with_ai)

            # Both files should be present
            assert "test_module.py" in output
            assert "utils.py" in output

            # Only test_module.py should have AI summary in appropriate formats
            if format_type == "json" and format_type in ["markdown", "json", "xml"]:
                json_data = json.loads(output)
                ai_file = next(f for f in json_data["files"] if f["file_path"] == "test_module.py")
                reg_file = next(f for f in json_data["files"] if f["file_path"] == "utils.py")
                assert "ai_summary" in ai_file
                assert "ai_summary" not in reg_file
