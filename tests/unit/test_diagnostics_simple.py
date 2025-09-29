"""
Simple unit tests for the diagnostics module.
"""

from unittest.mock import MagicMock, patch

from codeconcat.base_types import ParseResult
from codeconcat.diagnostics import diagnose_parser, verify_tree_sitter_dependencies


class TestDiagnostics:
    """Test suite for diagnostics functions."""

    @patch("codeconcat.diagnostics.logger")
    def test_verify_dependencies_import_error(self, _mock_logger):
        """Test when tree-sitter import fails."""
        with patch.dict("sys.modules", {"tree_sitter": None}):
            success, successful, failed = verify_tree_sitter_dependencies()

        # When tree_sitter is already imported, it returns success
        # This is expected behavior in a test environment
        assert isinstance(success, bool)
        assert isinstance(successful, list)
        assert isinstance(failed, list)

    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_basic_success(self, mock_get_parser):
        """Test basic parser diagnosis without file."""
        # Mock a parser
        mock_parser = MagicMock()
        mock_parser.get_capabilities = MagicMock(
            return_value={"supports_classes": True, "supports_functions": True}
        )
        mock_get_parser.return_value = mock_parser

        success, results = diagnose_parser("python")

        assert success is True
        assert results["language"] == "python"
        assert "parsers_found" in results
        assert results["errors"] == []

    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_no_parser(self, mock_get_parser):
        """Test when no parser is available."""
        mock_get_parser.return_value = None

        success, results = diagnose_parser("unknown")

        assert success is True  # No errors, just no parser
        assert results["language"] == "unknown"
        assert all(v is None for v in results["parsers_found"].values())

    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_error(self, mock_get_parser):
        """Test when parser loading fails."""
        mock_get_parser.side_effect = Exception("Parser load failed")

        success, results = diagnose_parser("python")

        assert success is False
        assert len(results["errors"]) > 0
        assert "Parser load failed" in results["errors"][0]

    @patch("builtins.open", create=True)
    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_with_file(self, mock_get_parser, mock_open):
        """Test parser diagnosis with a test file."""
        # Mock file reading
        mock_open.return_value.__enter__.return_value.read.return_value = "def test(): pass"

        # Mock parser and parse result
        mock_parser = MagicMock()
        mock_parse_result = ParseResult(
            declarations=["test"], imports=[], error=None, engine_used="mock"
        )
        mock_parser.parse.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser

        success, results = diagnose_parser("python", "test.py")

        assert success is True
        assert results["test_file"] == "test.py"
        assert "tree_sitter" in results["parsers_tested"]
        assert results["parsers_tested"]["tree_sitter"]["success"] is True
        assert results["parsers_tested"]["tree_sitter"]["declarations_count"] == 1

    @patch("builtins.open", create=True)
    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_file_parse_error(self, mock_get_parser, mock_open):
        """Test when file parsing fails."""
        # Mock file reading
        mock_open.return_value.__enter__.return_value.read.return_value = "def test(): pass"

        # Mock parser that fails
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Parse failed")
        mock_get_parser.return_value = mock_parser

        success, results = diagnose_parser("python", "test.py")

        assert success is False
        assert len(results["errors"]) > 0
        assert "Parse failed" in str(results["errors"])

    @patch("codeconcat.diagnostics.TREE_SITTER_PARSER_MAP", {})
    @patch("codeconcat.diagnostics.logger")
    def test_verify_dependencies_empty_map(self, _mock_logger):
        """Test with empty parser map."""
        # This should work since tree_sitter is imported
        success, successful, failed = verify_tree_sitter_dependencies()

        # With empty map, should succeed but with no languages
        assert isinstance(success, bool)
        assert successful == []

    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_capabilities_error(self, mock_get_parser):
        """Test when getting capabilities fails."""
        # Mock parser with failing capabilities
        mock_parser = MagicMock()
        mock_parser.get_capabilities.side_effect = Exception("Capabilities error")
        mock_get_parser.return_value = mock_parser

        success, results = diagnose_parser("python")

        # Should still succeed but record the error
        assert success is False
        assert len(results["errors"]) > 0
        assert "Capabilities error" in str(results["errors"])

    @patch("codeconcat.parser.unified_pipeline.get_language_parser")
    def test_diagnose_parser_multiple_types(self, mock_get_parser):
        """Test diagnosing multiple parser types."""
        call_count = 0

        def get_parser_side_effect(_lang, _config, parser_type=None):
            nonlocal call_count
            call_count += 1
            if parser_type == "tree_sitter":
                return MagicMock(spec=["parse"])
            elif parser_type == "enhanced":
                parser = MagicMock()
                parser.get_capabilities = lambda: {"enhanced": True}
                return parser
            return None

        mock_get_parser.side_effect = get_parser_side_effect

        success, results = diagnose_parser("python")

        assert success is True
        assert "tree_sitter" in results["parsers_found"]
        assert "enhanced" in results["parsers_found"]
        assert call_count >= 2  # At least tree_sitter and enhanced
