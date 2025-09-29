"""Test AI summary generation in the processing pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codeconcat.ai.base import SummarizationResult
from codeconcat.base_types import CodeConCatConfig, Declaration, ParsedFileData
from codeconcat.main import run_codeconcat
from codeconcat.processor.summarization_processor import SummarizationProcessor
from codeconcat.transformer.annotator import annotate


class TestAISummaryGeneration:
    """Test that AI summaries are generated during processing."""

    @pytest.fixture
    def test_config(self):
        """Create config with AI summary enabled."""
        return CodeConCatConfig(
            project_path=".",
            format="markdown",
            enable_ai_summary=True,
            ai_provider="anthropic",
            ai_api_key="test_key",
            ai_model="claude-3-haiku-20240307",
            include_file_summary=True,
            disable_progress_bar=True,
            disable_hints=True,
        )

    @pytest.fixture
    def sample_parsed_file(self):
        """Create a sample parsed file."""
        return ParsedFileData(
            file_path="example.py",
            content='''def process_data(items):
    """Process a list of data items."""
    results = []
    for item in items:
        if item.is_valid():
            results.append(item.transform())
    return results

class DataProcessor:
    """Main data processing class."""
    def __init__(self):
        self.processed_count = 0

    def process(self, data):
        """Process a single data item."""
        self.processed_count += 1
        return data.upper()
''',
            language="python",
            declarations=[
                Declaration(
                    kind="function",
                    name="process_data",
                    start_line=1,
                    end_line=7,
                    modifiers=set(),
                    docstring="Process a list of data items.",
                    children=[],
                ),
                Declaration(
                    kind="class",
                    name="DataProcessor",
                    start_line=9,
                    end_line=16,
                    modifiers=set(),
                    docstring="Main data processing class.",
                    children=[
                        Declaration(
                            kind="function",
                            name="__init__",
                            start_line=11,
                            end_line=12,
                            modifiers=set(),
                            children=[],
                        ),
                        Declaration(
                            kind="function",
                            name="process",
                            start_line=14,
                            end_line=16,
                            modifiers=set(),
                            docstring="Process a single data item.",
                            children=[],
                        ),
                    ],
                ),
            ],
            imports=[],
        )

    @pytest.mark.asyncio
    async def test_summarization_processor_generates_summaries(
        self, test_config, sample_parsed_file
    ):
        """Test that SummarizationProcessor actually generates AI summaries."""
        # Mock the AI provider
        mock_provider = MagicMock()
        mock_provider.summarize_code = AsyncMock(
            return_value=SummarizationResult(
                summary="This module implements data processing functionality with validation and transformation capabilities. The process_data function iterates through items, validates them, and applies transformations. The DataProcessor class provides stateful processing with counting.",
                tokens_used=150,
                cost_estimate=0.001,
                model_used="claude-3-haiku-20240307",
                cached=False,
                error=None,
            )
        )

        # Create processor with mocked provider
        processor = SummarizationProcessor(test_config)
        processor.ai_provider = mock_provider

        # Process the file
        result = await processor.process_file(sample_parsed_file)

        # Verify AI summary was added
        assert hasattr(result, "ai_summary")
        assert result.ai_summary is not None
        assert "data processing functionality" in result.ai_summary
        assert "validation and transformation" in result.ai_summary

        # Verify the provider was called
        mock_provider.summarize_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_processing_with_ai_summaries(self, test_config):
        """Test that batch processing generates summaries for multiple files."""
        # Create multiple parsed files with sufficient content
        files = [
            ParsedFileData(
                file_path=f"file{i}.py",
                content=f"""def function{i}(data):
    '''Process data for module {i}.'''
    result = []
    for item in data:
        if item > {i}:
            result.append(item * {i + 1})
    return result

class Module{i}:
    '''Module {i} implementation.'''
    def __init__(self):
        self.value = {i}

    def process(self):
        return self.value * 2
""",
                language="python",
                declarations=[
                    Declaration(
                        kind="function",
                        name=f"function{i}",
                        start_line=1,
                        end_line=7,
                        modifiers=set(),
                        docstring=f"Process data for module {i}.",
                        children=[],
                    ),
                    Declaration(
                        kind="class",
                        name=f"Module{i}",
                        start_line=9,
                        end_line=15,
                        modifiers=set(),
                        docstring=f"Module {i} implementation.",
                        children=[],
                    ),
                ],
                imports=[],
            )
            for i in range(3)
        ]

        # Mock the AI provider
        mock_provider = MagicMock()
        mock_provider.summarize_code = AsyncMock(
            side_effect=[
                SummarizationResult(
                    summary=f"Summary for file {i}",
                    tokens_used=50,
                    cost_estimate=0.0005,
                    model_used="claude-3-haiku-20240307",
                    cached=False,
                    error=None,
                )
                for i in range(3)
            ]
        )

        # Create processor with mocked provider
        processor = SummarizationProcessor(test_config)
        processor.ai_provider = mock_provider

        # Process the batch
        results = await processor.process_batch(files)

        # Verify all files got summaries
        assert len(results) == 3
        for i, result in enumerate(results):
            assert hasattr(result, "ai_summary")
            assert result.ai_summary == f"Summary for file {i}"

        # Verify the provider was called for each file
        assert mock_provider.summarize_code.call_count == 3

    def test_ai_summary_passed_to_annotated_file(self, test_config, sample_parsed_file):
        """Test that AI summaries are preserved when converting to AnnotatedFileData."""
        # Add an AI summary to the parsed file
        sample_parsed_file.ai_summary = "This is an AI-generated summary of the code."

        # Annotate the file
        annotated = annotate(sample_parsed_file, test_config)

        # Verify AI summary is preserved
        assert annotated.ai_summary == "This is an AI-generated summary of the code."
        # Verify regular summary is still generated
        assert annotated.summary == "Contains 1 functions, 1 classes"

    @patch("codeconcat.processor.summarization_processor.get_ai_provider")
    def test_summarization_with_provider_initialization(self, mock_get_provider, test_config):
        """Test that summarization processor initializes the AI provider correctly."""
        # Mock the provider factory
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        # Create processor
        processor = SummarizationProcessor(test_config)

        # Verify provider was initialized
        assert processor.ai_provider == mock_provider
        mock_get_provider.assert_called_once()

        # Check the config passed to the provider
        call_args = mock_get_provider.call_args[0][0]
        assert call_args.provider_type.value == "anthropic"
        assert call_args.api_key == "test_key"
        assert call_args.model == "claude-3-haiku-20240307"

    def test_summarization_disabled_when_no_api_key(self):
        """Test that summarization is disabled when no API key is provided."""
        config = CodeConCatConfig(
            project_path=".",
            format="markdown",
            enable_ai_summary=True,
            ai_provider="anthropic",
            ai_api_key=None,  # No API key
            ai_model="claude-3-haiku-20240307",
        )

        with patch(
            "codeconcat.processor.summarization_processor.get_ai_provider"
        ) as mock_get_provider:
            mock_get_provider.side_effect = Exception("No API key provided")

            processor = SummarizationProcessor(config)

            # Verify provider is None when initialization fails
            assert processor.ai_provider is None

    @pytest.mark.asyncio
    async def test_summarization_handles_errors_gracefully(self, test_config, sample_parsed_file):
        """Test that summarization handles AI provider errors gracefully."""
        # Mock the AI provider to return an error
        mock_provider = MagicMock()
        mock_provider.summarize_code = AsyncMock(
            return_value=SummarizationResult(
                summary=None,
                tokens_used=0,
                cost_estimate=0,
                model_used="claude-3-haiku-20240307",
                cached=False,
                error="API rate limit exceeded",
            )
        )

        # Create processor with mocked provider
        processor = SummarizationProcessor(test_config)
        processor.ai_provider = mock_provider

        # Process the file
        result = await processor.process_file(sample_parsed_file)

        # Verify no AI summary was added when there's an error
        assert not hasattr(result, "ai_summary") or result.ai_summary is None

        # Verify the provider was called
        mock_provider.summarize_code.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarization_skips_small_files(self, test_config):
        """Test that summarization skips files that are too small."""
        # Create a very small file (less than 5 lines)
        small_file = ParsedFileData(
            file_path="tiny.py",
            content="x = 1\ny = 2\nz = x + y",
            language="python",
            declarations=[],
            imports=[],
        )

        # Mock the AI provider
        mock_provider = MagicMock()
        mock_provider.summarize_code = AsyncMock()

        # Create processor with mocked provider
        processor = SummarizationProcessor(test_config)
        processor.ai_provider = mock_provider

        # Process the file
        result = await processor.process_file(small_file)

        # Verify no AI summary was added for small files
        assert not hasattr(result, "ai_summary") or result.ai_summary is None

        # Verify the provider was NOT called for small files
        mock_provider.summarize_code.assert_not_called()


class TestEndToEndAISummaryGeneration:
    """Test AI summary generation in the complete pipeline."""

    @patch("codeconcat.processor.summarization_processor.create_summarization_processor")
    @patch("codeconcat.collector.local_collector.collect_local_files")
    def test_main_pipeline_with_ai_summaries(self, mock_collect, mock_create_summarizer):
        """Test that the main pipeline generates and preserves AI summaries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('''def main():
    """Main entry point."""
    print("Hello, world!")
    return 0

def helper():
    """Helper function."""
    return 42
''')

            # Mock file collection
            mock_collect.return_value = [str(test_file)]

            # Mock summarization processor
            mock_summarizer = MagicMock()

            async def mock_process_batch(files):
                # Add AI summaries to the files
                for f in files:
                    f.ai_summary = (
                        f"AI summary for {f.file_path}: This file contains utility functions."
                    )
                return files

            mock_summarizer.process_batch = mock_process_batch
            mock_summarizer.cleanup = AsyncMock()
            mock_create_summarizer.return_value = mock_summarizer

            # Create config with AI summaries enabled
            config = CodeConCatConfig(
                project_path=tmpdir,
                format="markdown",
                enable_ai_summary=True,
                ai_provider="anthropic",
                ai_api_key="test_key",
                ai_model="claude-3-haiku-20240307",
                include_file_summary=True,
                disable_progress_bar=True,
                disable_hints=True,
            )

            # Run the pipeline
            output = run_codeconcat(config)

            # Verify the summarizer was created and called
            mock_create_summarizer.assert_called_once_with(config)

            # Verify AI summary appears in the output
            assert "AI Summary" in output or "AI summary for" in output
            # The actual summary text might be in different formats depending on the writer

    def test_config_flag_enables_ai_summaries(self):
        """Test that the enable_ai_summary flag controls AI summary generation."""
        # Config with AI summaries disabled
        config_disabled = CodeConCatConfig(
            project_path=".",
            format="markdown",
            enable_ai_summary=False,  # Disabled
            ai_provider="anthropic",
            ai_api_key="test_key",
        )

        with patch(
            "codeconcat.processor.summarization_processor.get_ai_provider"
        ) as mock_get_provider:
            from codeconcat.processor.summarization_processor import create_summarization_processor

            # Should return None when disabled
            processor = create_summarization_processor(config_disabled)
            assert processor is None
            mock_get_provider.assert_not_called()

        # Config with AI summaries enabled
        config_enabled = CodeConCatConfig(
            project_path=".",
            format="markdown",
            enable_ai_summary=True,  # Enabled
            ai_provider="anthropic",
            ai_api_key="test_key",
        )

        with patch(
            "codeconcat.processor.summarization_processor.get_ai_provider"
        ) as mock_get_provider:
            mock_get_provider.return_value = MagicMock()

            # Should create processor when enabled
            processor = create_summarization_processor(config_enabled)
            assert processor is not None
            mock_get_provider.assert_called_once()
