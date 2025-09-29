"""Integration tests for AI meta-overview functionality."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codeconcat.ai import SummarizationResult
from codeconcat.ai.base import AIProvider
from codeconcat.base_types import CodeConCatConfig
from codeconcat.processor.summarization_processor import SummarizationProcessor


@pytest.fixture
def mock_ai_provider():
    """Create a mock AI provider that simulates real behavior."""
    provider = MagicMock(spec=AIProvider)

    # Mock file summaries
    async def mock_summarize_code(code, language, context=None, max_length=None):  # noqa: ARG001
        file_path = context.get("file_path", "unknown") if context else "unknown"

        # Return different summaries based on file path
        if "main.py" in file_path:
            summary = "Main application entry point with command-line interface and core application logic."
        elif "utils.py" in file_path:
            summary = (
                "Utility functions for string manipulation, data validation, and file operations."
            )
        elif "config.py" in file_path:
            summary = "Configuration management with environment variables and settings validation."
        else:
            summary = f"Code file implementing {language} functionality."

        return SummarizationResult(
            summary=summary, tokens_used=100, model_used="mock-model", provider="mock", cached=False
        )

    # Mock meta-overview generation
    async def mock_generate_meta_overview(file_summaries, custom_prompt=None, max_tokens=None):  # noqa: ARG001
        if custom_prompt and "CUSTOM_TEST" in custom_prompt:
            overview = "CUSTOM META-OVERVIEW: Test project with custom processing logic."
        else:
            overview = (
                "This codebase implements a Python application with the following key components:\n\n"
                "1. **Architecture**: Modular design with separate concerns for configuration, utilities, and main logic\n"
                "2. **Key Components**: Main entry point (main.py), utility functions (utils.py), and configuration management (config.py)\n"
                "3. **Technologies**: Python with modern async/await patterns and comprehensive error handling\n"
                "4. **Design Patterns**: Follows SOLID principles with dependency injection and factory patterns\n"
                "5. **Areas for Improvement**: Consider adding more comprehensive test coverage and documentation"
            )

        return SummarizationResult(
            summary=overview,
            tokens_used=200,
            model_used="mock-model",
            provider="mock",
            cached=False,
        )

    provider.summarize_code = mock_summarize_code
    provider.generate_meta_overview = mock_generate_meta_overview
    provider.close = AsyncMock()

    return provider


@pytest.fixture
def test_project_files():
    """Create test project files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create test Python files
        (project_dir / "main.py").write_text(
            '''
"""Main application module."""

import sys
from config import load_config
from utils import process_data

def main():
    """Main entry point."""
    config = load_config()
    data = sys.stdin.read()
    result = process_data(data, config)
    print(result)

if __name__ == "__main__":
    main()
'''
        )

        (project_dir / "utils.py").write_text(
            '''
"""Utility functions."""

def process_data(data, config):
    """Process input data according to config."""
    if config.get("uppercase"):
        return data.upper()
    return data.lower()

def validate_input(data):
    """Validate input data."""
    return bool(data and data.strip())
'''
        )

        (project_dir / "config.py").write_text(
            '''
"""Configuration module."""

import os

def load_config():
    """Load configuration from environment."""
    return {
        "uppercase": os.getenv("UPPERCASE", "false").lower() == "true",
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }
'''
        )

        yield project_dir


@pytest.mark.asyncio
async def test_meta_overview_generation(test_project_files, mock_ai_provider):
    """Test that meta-overview is generated from file summaries."""
    with patch(
        "codeconcat.processor.summarization_processor.get_ai_provider",
        return_value=mock_ai_provider,
    ):
        config = CodeConCatConfig(
            target_path=str(test_project_files),
            format="markdown",
            enable_ai_summary=True,
            ai_meta_overview=True,
            ai_provider="openai",  # Use valid provider name; get_ai_provider is patched
            ai_model="mock-model",
        )

        processor = SummarizationProcessor(config)

        # Create mock parsed files
        from codeconcat.base_types import ParsedFileData

        files = [
            ParsedFileData(
                file_path="main.py",
                language="python",
                content=(test_project_files / "main.py").read_text(),
                imports=[],
                declarations=[],
            ),
            ParsedFileData(
                file_path="utils.py",
                language="python",
                content=(test_project_files / "utils.py").read_text(),
                imports=[],
                declarations=[],
            ),
            ParsedFileData(
                file_path="config.py",
                language="python",
                content=(test_project_files / "config.py").read_text(),
                imports=[],
                declarations=[],
            ),
        ]

        # Process files
        processed_files = await processor.process_batch(files)

        # Check that all files have summaries
        for file in processed_files:
            assert hasattr(file, "ai_summary")
            assert file.ai_summary is not None
            assert len(file.ai_summary) > 0

        # Check that meta-overview was generated and stored
        assert hasattr(processed_files[0], "ai_metadata")
        assert processed_files[0].ai_metadata is not None
        assert "meta_overview" in processed_files[0].ai_metadata
        meta_overview = processed_files[0].ai_metadata["meta_overview"]

        assert meta_overview is not None
        assert "Architecture" in meta_overview
        assert "Key Components" in meta_overview
        assert "main.py" in meta_overview


@pytest.mark.asyncio
async def test_meta_overview_custom_prompt(test_project_files, mock_ai_provider):
    """Test meta-overview with custom prompt."""
    with patch(
        "codeconcat.processor.summarization_processor.get_ai_provider",
        return_value=mock_ai_provider,
    ):
        config = CodeConCatConfig(
            target_path=str(test_project_files),
            format="markdown",
            enable_ai_summary=True,
            ai_meta_overview=True,
            ai_meta_overview_prompt="CUSTOM_TEST: Generate a brief overview",
            ai_provider="openai",  # Use valid provider name; get_ai_provider is patched
            ai_model="mock-model",
        )

        processor = SummarizationProcessor(config)

        # Create mock parsed files
        from codeconcat.base_types import ParsedFileData

        files = [
            ParsedFileData(
                file_path="main.py",
                language="python",
                content=(test_project_files / "main.py").read_text(),
                imports=[],
                declarations=[],
            ),
        ]

        # Process files
        processed_files = await processor.process_batch(files)

        # Check that custom prompt was used
        assert hasattr(processed_files[0], "ai_metadata")
        assert processed_files[0].ai_metadata is not None
        meta_overview = processed_files[0].ai_metadata.get("meta_overview")
        assert meta_overview is not None
        assert "CUSTOM META-OVERVIEW" in meta_overview


@pytest.mark.asyncio
async def test_meta_overview_disabled(test_project_files, mock_ai_provider):
    """Test that meta-overview is not generated when disabled."""
    with patch(
        "codeconcat.processor.summarization_processor.get_ai_provider",
        return_value=mock_ai_provider,
    ):
        config = CodeConCatConfig(
            target_path=str(test_project_files),
            format="markdown",
            enable_ai_summary=True,
            ai_meta_overview=False,  # Disabled
            ai_provider="openai",  # Use valid provider name; get_ai_provider is patched
            ai_model="mock-model",
        )

        processor = SummarizationProcessor(config)

        # Create mock parsed files
        from codeconcat.base_types import ParsedFileData

        files = [
            ParsedFileData(
                file_path="main.py",
                language="python",
                content=(test_project_files / "main.py").read_text(),
                imports=[],
                declarations=[],
            ),
        ]

        # Process files
        processed_files = await processor.process_batch(files)

        # Check that file has summary but no meta-overview
        assert hasattr(processed_files[0], "ai_summary")
        assert processed_files[0].ai_summary is not None

        # Check that no meta-overview was generated
        if hasattr(processed_files[0], "ai_metadata") and processed_files[0].ai_metadata:
            assert "meta_overview" not in processed_files[0].ai_metadata


@pytest.mark.asyncio
async def test_meta_overview_no_summaries(test_project_files):
    """Test that meta-overview handles case with no file summaries."""
    # Create a provider that doesn't generate file summaries
    provider = MagicMock(spec=AIProvider)
    provider.summarize_code = AsyncMock(
        return_value=SummarizationResult(summary="", error="Test error")
    )
    provider.generate_meta_overview = AsyncMock()
    provider.close = AsyncMock()

    with patch(
        "codeconcat.processor.summarization_processor.get_ai_provider", return_value=provider
    ):
        config = CodeConCatConfig(
            target_path=str(test_project_files),
            format="markdown",
            enable_ai_summary=True,
            ai_meta_overview=True,
            ai_provider="openai",  # Use valid provider name; get_ai_provider is patched
            ai_model="mock-model",
        )

        processor = SummarizationProcessor(config)

        # Create mock parsed files
        from codeconcat.base_types import ParsedFileData

        files = [
            ParsedFileData(
                file_path="main.py",
                language="python",
                content="test content",
                imports=[],
                declarations=[],
            ),
        ]

        # Process files
        _ = await processor.process_batch(files)

        # Meta-overview should not be called since no file summaries exist
        provider.generate_meta_overview.assert_not_called()


def test_meta_overview_in_markdown_output(test_project_files, mock_ai_provider):
    """Test that meta-overview appears in markdown output."""
    with tempfile.TemporaryDirectory() as output_dir:
        output_file = Path(output_dir) / "output.md"

        with patch(
            "codeconcat.processor.summarization_processor.get_ai_provider",
            return_value=mock_ai_provider,
        ):
            # Run codeconcat with meta-overview enabled
            config = {
                "target_path": str(test_project_files),
                "format": "markdown",
                "output": str(output_file),
                "enable_ai_summary": True,
                "ai_meta_overview": True,
                "ai_meta_overview_position": "top",
                "ai_provider": "openai",  # Use valid provider name; get_ai_provider is patched
                "ai_model": "mock-model",
                "verbose": False,
            }

            # Mock the actual codeconcat run to generate output with meta-overview
            from codeconcat.base_types import ParsedFileData
            from codeconcat.writer.markdown_writer import write_markdown

            # Create test data with meta-overview
            test_files = [
                ParsedFileData(
                    file_path="main.py",
                    language="python",
                    content="test content",
                    imports=[],
                    declarations=[],
                    ai_summary="Main application entry point.",
                    ai_metadata={
                        "meta_overview": "Test meta-overview content with architecture details."
                    },
                ),
            ]

            config_obj = CodeConCatConfig(**config)
            output = write_markdown(test_files, config_obj)

            # Check that meta-overview is in the output
            assert "AI Meta-Overview" in output
            assert "Test meta-overview content" in output
            assert "architecture details" in output

            # Check position
            lines = output.split("\n")
            meta_index = next(i for i, line in enumerate(lines) if "AI Meta-Overview" in line)
            toc_index = next(i for i, line in enumerate(lines) if "Table of Contents" in line)

            if config["ai_meta_overview_position"] == "top":
                assert meta_index < toc_index


def test_meta_overview_position_bottom(test_project_files):
    """Test that meta-overview can be positioned at bottom."""
    from codeconcat.base_types import ParsedFileData
    from codeconcat.writer.markdown_writer import write_markdown

    # Create test data with meta-overview
    test_files = [
        ParsedFileData(
            file_path="main.py",
            language="python",
            content="test content",
            imports=[],
            declarations=[],
            ai_summary="Main application entry point.",
            ai_metadata={"meta_overview": "Test meta-overview at bottom."},
        ),
    ]

    config = CodeConCatConfig(
        target_path=str(test_project_files),
        format="markdown",
        ai_meta_overview_position="bottom",
    )

    output = write_markdown(test_files, config)

    # Check that meta-overview is in the output
    assert "AI Meta-Overview" in output
    assert "Test meta-overview at bottom" in output

    # Check position - should be after file details
    lines = output.split("\n")
    meta_index = next(i for i, line in enumerate(lines) if "AI Meta-Overview" in line)
    details_index = next(i for i, line in enumerate(lines) if "File Details" in line)

    assert meta_index > details_index
