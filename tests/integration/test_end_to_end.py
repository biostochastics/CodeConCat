#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for CodeConCat.

Tests the end-to-end processing flow from parsing code files through
annotation, rendering, and output creation.
"""

import os
import tempfile
import logging
import pytest
import json

from codeconcat.base_types import (
    CodeConCatConfig,
    AnnotatedFileData,
    TokenStats,
    ParsedFileData,
)
from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging
from codeconcat.parser.file_parser import parse_code_files

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestEndToEndProcessing:
    """Test end-to-end processing with various integration points."""

    @pytest.fixture
    def test_files_dir(self) -> str:
        """Create temporary test files and return their directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Python file
            with open(os.path.join(temp_dir, "test_file.py"), "w") as f:
                f.write(
                    """
# A simple test file

def sample_function():
    \"\"\"This is a docstring.\"\"\"
    return "Hello, World!"

class SampleClass:
    \"\"\"A sample class.\"\"\"
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
"""
                )

            # Create a Markdown doc file
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write(
                    """
# Test Project

This is a test project for integration testing.

## Features

- Feature 1
- Feature 2
"""
                )

            yield temp_dir

    @pytest.fixture
    def config(self) -> CodeConCatConfig:
        """Fixture providing a test configuration."""
        # Use ConfigBuilder to create a consistent configuration
        builder = ConfigBuilder()
        builder.with_defaults()
        builder.with_preset("medium")

        # Override some settings for testing
        cli_args = {
            "output": "test_output.md",
            "format": "markdown",
            "enable_token_counting": True,
            "include_file_summary": True,
            "disable_tree": True,  # Use regex parsers for predictable testing
        }

        builder.with_cli_args(cli_args)
        return builder.build()

    def test_file_parsing_to_annotated_data(self, test_files_dir, config):
        """Test parsing files into annotated data structures."""
        # Prepare the file for parsing
        py_file_path = os.path.join(test_files_dir, "test_file.py")

        # Create a ParsedFileData object for the file
        parsed_file_data = ParsedFileData(
            file_path=py_file_path, content=open(py_file_path, "r").read(), language="python"
        )

        # Parse the file using parse_code_files
        parsed_files, errors = parse_code_files([parsed_file_data], config)

        # Verify the parse result
        assert len(parsed_files) == 1
        assert len(errors) == 0
        parsed_data = parsed_files[0]
        assert parsed_data is not None
        assert parsed_data.file_path == py_file_path
        assert parsed_data.language == "python"
        assert len(parsed_data.parse_result.declarations) > 0

        # Find specific declarations
        func_decl = None
        class_decl = None
        for decl in parsed_data.parse_result.declarations:
            if decl.name == "sample_function":
                func_decl = decl
            elif decl.name == "SampleClass":
                class_decl = decl

        # Check the function declaration
        assert func_decl is not None
        assert func_decl.docstring is not None
        assert "This is a docstring" in func_decl.docstring

        # Check the class declaration
        assert class_decl is not None
        assert class_decl.docstring is not None
        assert "A sample class" in class_decl.docstring
        assert len(class_decl.children) == 2  # __init__ and get_value

    def test_doc_file_parsing(self, test_files_dir, config):
        """Test parsing documentation files."""
        # Import here to avoid circular imports
        from codeconcat.parser.doc_extractor import extract_docs

        # Create a Markdown file for doc extraction
        md_file_path = os.path.join(test_files_dir, "README.md")

        # Make sure .md is in doc_extensions
        if ".md" not in config.doc_extensions:
            config.doc_extensions.append(".md")

        # Extract docs from the test file
        doc_data_list = extract_docs([md_file_path], config)

        # Verify the extract result
        assert len(doc_data_list) == 1
        doc_data = doc_data_list[0]
        assert doc_data is not None
        assert doc_data.file_path == md_file_path
        assert doc_data.doc_type == "md"  # Extension is used as doc_type
        assert "# Test Project" in doc_data.content

    def test_rendering_pipeline_markdown(self, test_files_dir, config):
        """Test the rendering pipeline for Markdown output."""
        # Import relevant modules
        from codeconcat.writer.markdown_writer import write_markdown

        # Prepare file for parsing
        py_file_path = os.path.join(test_files_dir, "test_file.py")
        file_content = open(py_file_path, "r").read()

        # Create ParsedFileData object
        parsed_file_data = ParsedFileData(
            file_path=py_file_path, content=file_content, language="python"
        )

        # Parse the file
        parsed_files, errors = parse_code_files([parsed_file_data], config)
        assert len(parsed_files) == 1
        assert len(errors) == 0
        parsed_data = parsed_files[0]

        # Create annotated data
        annotated_data = AnnotatedFileData(
            file_path=parsed_data.file_path,
            language=parsed_data.language,
            content=parsed_data.content,
            annotated_content=parsed_data.content,  # Same for test
            summary="Sample Python file for testing",
            declarations=parsed_data.parse_result.declarations,
            imports=parsed_data.imports,
            token_stats=TokenStats(
                gpt3_tokens=100, gpt4_tokens=120, davinci_tokens=90, claude_tokens=110
            ),
            tags=["test", "python"],
        )

        # Set the format explicitly
        config.format = "markdown"

        # Generate markdown output
        output = write_markdown([annotated_data], config)

        # Verify output
        assert isinstance(output, str)
        assert "# CodeConCat Output" in output
        assert "## File: " in output
        assert "Sample Python file for testing" in output
        assert "```python" in output
        assert "def sample_function()" in output
        assert "class SampleClass" in output

    def test_rendering_pipeline_json(self, test_files_dir, config):
        """Test the rendering pipeline for JSON output."""
        # Import relevant modules
        from codeconcat.writer.json_writer import write_json

        # Prepare file for parsing
        py_file_path = os.path.join(test_files_dir, "test_file.py")
        file_content = open(py_file_path, "r").read()

        # Create ParsedFileData object
        parsed_file_data = ParsedFileData(
            file_path=py_file_path, content=file_content, language="python"
        )

        # Parse the file
        parsed_files, errors = parse_code_files([parsed_file_data], config)
        assert len(parsed_files) == 1
        assert len(errors) == 0
        parsed_data = parsed_files[0]

        # Create annotated data
        annotated_data = AnnotatedFileData(
            file_path=parsed_data.file_path,
            language=parsed_data.language,
            content=parsed_data.content,
            annotated_content=parsed_data.content,  # Same for test
            summary="Sample Python file for testing",
            declarations=parsed_data.parse_result.declarations,
            imports=parsed_data.imports,
            token_stats=TokenStats(
                gpt3_tokens=100, gpt4_tokens=120, davinci_tokens=90, claude_tokens=110
            ),
            tags=["test", "python"],
        )

        # Set the format and enable token counting
        config.format = "json"
        config.enable_token_counting = True

        # Generate JSON output
        output = write_json([annotated_data], config)

        # Verify output
        assert isinstance(output, str)

        # Parse the JSON to verify structure
        json_data = json.loads(output)
        assert "files" in json_data
        assert len(json_data["files"]) == 1

        item = json_data["files"][0]
        assert item["file_path"] == py_file_path
        assert item["language"] == "python"
        assert "declarations" in item
        assert "token_stats" in item

    def test_config_builder_integration(self):
        """Test that ConfigBuilder properly integrates with the processing pipeline."""
        # Create a temporary YAML config file
        yaml_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".yml", mode="w", delete=False) as yaml_file:
                yaml_file.write(
                    """
                # Test YAML config
                target_path: "./src"
                include_paths:
                  - src/
                  - tests/
                exclude_paths:
                  - node_modules/
                enable_token_counting: true
                """
                )
                yaml_path = yaml_file.name

            # Create a builder with all stages to test the API chaining
            builder = ConfigBuilder()
            result1 = builder.with_defaults()
            result2 = builder.with_preset("lean")
            result3 = builder.with_yaml_config(yaml_path)
            result4 = builder.with_cli_args({"format": "json", "output": "cli_output.json"})

            # Verify method chaining works correctly
            assert result1 is builder
            assert result2 is builder
            assert result3 is builder
            assert result4 is builder

            # Build the config
            config = builder.build()

            # Verify we got a valid configuration object
            assert isinstance(config, CodeConCatConfig)

            # Verify key configuration attributes exist
            assert hasattr(config, "target_path")
            assert hasattr(config, "format")
            assert hasattr(config, "output")
            assert hasattr(config, "parser_engine")
            assert hasattr(config, "include_file_summary")
            assert hasattr(config, "remove_comments")

            # target_path should be a string or Path object
            assert config.target_path is not None

            # Test some expected basic behavior
            assert config.format in ["json", "markdown", "text", "xml"]  # Should be a valid format
            assert isinstance(config.include_paths, list)  # Should be a list
            assert isinstance(config.exclude_paths, list)  # Should be a list
        finally:
            # Clean up the temporary file
            if yaml_path:
                os.unlink(yaml_path)


if __name__ == "__main__":
    unittest.main(["-v", __file__])
