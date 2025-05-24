"""Tests for the enhanced parsing pipeline."""

import pytest
from unittest.mock import MagicMock, patch, call
import logging

from codeconcat.base_types import (
    CodeConCatConfig, 
    ParsedFileData, 
    ParseResult,
    Declaration,
    EnhancedParserInterface
)
from codeconcat.parser.enhanced_pipeline import (
    enhanced_parse_pipeline,
    process_with_progress
)
from codeconcat.errors import (
    ParserError,
    LanguageParserError,
    UnsupportedLanguageError,
    FileProcessingError
)


class MockEnhancedParser(EnhancedParserInterface):
    """Mock enhanced parser for testing."""
    
    def __init__(self, validate_result=True, parse_result=None):
        self.validate_result = validate_result
        self.parse_result = parse_result
    
    def parse(self, content: str, file_path: str = "") -> ParseResult:
        return self.parse_result or ParseResult(
            declarations=[Declaration(name="test", declaration_type="function", line_number=1)],
            imports=[],
            error=None
        )
    
    def validate(self) -> bool:
        return self.validate_result
    
    def get_capabilities(self) -> dict:
        return {"test": True}


class TestEnhancedPipeline:
    """Test suite for enhanced parsing pipeline."""

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_successful_tree_sitter_parsing(self, mock_get_parser, mock_progress):
        """Test successful parsing with tree-sitter parser."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock tree-sitter parser
        mock_parser = MockEnhancedParser()
        mock_get_parser.return_value = mock_parser
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 1
        assert len(errors) == 0
        assert parsed_files[0].parse_result is not None
        assert parsed_files[0].parse_result.declarations[0].name == "test"
        mock_get_parser.assert_called_once_with("python", config, parser_type="tree_sitter")

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_fallback_to_enhanced_regex(self, mock_get_parser, mock_progress):
        """Test fallback from tree-sitter to enhanced regex parser."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock parsers - tree-sitter fails, enhanced succeeds
        mock_get_parser.side_effect = [
            None,  # Tree-sitter returns None
            MockEnhancedParser(),  # Enhanced parser succeeds
        ]
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 1
        assert len(errors) == 0
        assert mock_get_parser.call_count == 2
        mock_get_parser.assert_any_call("python", config, parser_type="tree_sitter")
        mock_get_parser.assert_any_call("python", config, parser_type="enhanced")

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_fallback_to_standard_regex(self, mock_get_parser, mock_progress):
        """Test fallback through all parser types."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock standard parser (not enhanced)
        standard_parser = MagicMock()
        standard_parser.parse.return_value = ParseResult(
            declarations=[Declaration(name="standard", declaration_type="function", line_number=1)],
            imports=[],
            error=None
        )
        
        # Mock parsers - tree-sitter and enhanced fail, standard succeeds
        mock_get_parser.side_effect = [
            None,  # Tree-sitter returns None
            None,  # Enhanced returns None
            standard_parser  # Standard parser succeeds
        ]
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 1
        assert len(errors) == 0
        assert parsed_files[0].parse_result.declarations[0].name == "standard"
        assert mock_get_parser.call_count == 3

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    def test_skip_unknown_language(self, mock_progress):
        """Test skipping files with unknown language."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.txt",
            content="some content",
            language="unknown"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_progress_bar = False
        
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 0
        assert len(errors) == 0

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    def test_skip_excluded_language(self, mock_progress):
        """Test skipping files with excluded languages."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = ["python"]
        
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 0
        assert len(errors) == 0

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    def test_include_languages_filter(self, mock_progress):
        """Test filtering by include_languages."""
        # Setup
        files = [
            ParsedFileData(file_path="/test/file.py", content="python", language="python"),
            ParsedFileData(file_path="/test/file.js", content="javascript", language="javascript"),
        ]
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_progress_bar = False
        config.include_languages = ["python"]
        config.exclude_languages = []
        
        mock_progress.return_value = files
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline(files, config)
        
        # Assert - only python file should be processed
        assert len(parsed_files) == 0  # No parser mocked, so no successful parses
        assert len(errors) == 1  # Only python file attempted

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    def test_missing_file_data(self, mock_progress):
        """Test handling of missing file path or content."""
        # Setup
        files = [
            ParsedFileData(file_path=None, content="content", language="python"),
            ParsedFileData(file_path="/test/file.py", content=None, language="python"),
        ]
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_progress_bar = False
        
        mock_progress.return_value = files
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline(files, config)
        
        # Assert
        assert len(parsed_files) == 0
        assert len(errors) == 2
        assert all(isinstance(e, ParserError) for e in errors)

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_parser_validation_failure(self, mock_get_parser, mock_progress):
        """Test handling of parser validation failure."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock parser that fails validation
        mock_parser = MockEnhancedParser(validate_result=False)
        mock_get_parser.return_value = mock_parser
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 0
        assert len(errors) == 1
        assert isinstance(errors[0], UnsupportedLanguageError)

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_parser_with_error_result(self, mock_get_parser, mock_progress):
        """Test handling of parser that returns error in parse result."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock parser that returns error
        error_result = ParseResult(
            declarations=[Declaration(name="partial", declaration_type="function", line_number=1)],
            imports=[],
            error="Partial parse error"
        )
        mock_parser = MockEnhancedParser(parse_result=error_result)
        mock_get_parser.return_value = mock_parser
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert - partial results are kept
        assert len(parsed_files) == 1
        assert len(errors) == 1
        assert isinstance(errors[0], LanguageParserError)
        assert parsed_files[0].parse_result.declarations[0].name == "partial"

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_unexpected_exception_handling(self, mock_get_parser, mock_progress):
        """Test handling of unexpected exceptions during parsing."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock parser that raises exception
        mock_get_parser.side_effect = Exception("Unexpected error")
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert
        assert len(parsed_files) == 0
        assert len(errors) == 1
        assert isinstance(errors[0], FileProcessingError)
        assert "Unexpected error" in str(errors[0])

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    def test_disable_tree_sitter(self, mock_get_parser, mock_progress):
        """Test parsing with tree-sitter disabled."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = True
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock enhanced parser
        mock_parser = MockEnhancedParser()
        mock_get_parser.return_value = mock_parser
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert - should skip tree-sitter and go directly to enhanced
        assert len(parsed_files) == 1
        assert len(errors) == 0
        mock_get_parser.assert_called_once_with("python", config, parser_type="enhanced")

    def test_process_with_progress_enabled(self):
        """Test process_with_progress with progress bar enabled."""
        items = [1, 2, 3]
        
        with patch('codeconcat.parser.enhanced_pipeline.tqdm') as mock_tqdm:
            mock_tqdm.return_value = items
            result = process_with_progress(items, "Testing", False, "item")
            
            mock_tqdm.assert_called_once_with(
                items,
                desc="Testing",
                unit="item",
                total=3,
                disable=False
            )
            assert result == items

    def test_process_with_progress_disabled(self):
        """Test process_with_progress with progress bar disabled."""
        items = [1, 2, 3]
        
        with patch('codeconcat.parser.enhanced_pipeline.tqdm') as mock_tqdm:
            mock_tqdm.return_value = items
            result = process_with_progress(items, "Testing", True, "file")
            
            mock_tqdm.assert_called_once_with(
                items,
                desc="Testing",
                unit="file",
                total=3,
                disable=True
            )
            assert result == items

    @patch('codeconcat.parser.enhanced_pipeline.process_with_progress')
    @patch('codeconcat.parser.enhanced_pipeline.get_language_parser')
    @patch('codeconcat.parser.enhanced_pipeline.logger')
    def test_logging_levels(self, mock_logger, mock_get_parser, mock_progress):
        """Test that appropriate logging levels are used."""
        # Setup
        file_data = ParsedFileData(
            file_path="/test/file.py",
            content="def test(): pass",
            language="python"
        )
        config = MagicMock(spec=CodeConCatConfig)
        config.disable_tree = False
        config.disable_progress_bar = False
        config.include_languages = None
        config.exclude_languages = []
        
        # Mock successful parser
        mock_parser = MockEnhancedParser()
        mock_get_parser.return_value = mock_parser
        mock_progress.return_value = [file_data]
        
        # Execute
        parsed_files, errors = enhanced_parse_pipeline([file_data], config)
        
        # Assert logging
        assert mock_logger.info.called
        assert mock_logger.debug.called
        # Check that info is used for start/end messages
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Starting enhanced parsing pipeline" in msg for msg in info_calls)
        assert any("Enhanced parsing pipeline completed" in msg for msg in info_calls)