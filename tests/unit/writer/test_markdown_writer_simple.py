"""Simple tests for markdown writer functionality."""

from unittest.mock import Mock, patch

from codeconcat.writer.markdown_writer import (
    write_markdown,
    count_tokens,
    is_test_or_config_file,
    _generate_anchor_name,
)
from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    Declaration,
)


class TestMarkdownWriterSimple:
    """Simple test suite for markdown writer."""

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        with patch("tiktoken.get_encoding") as mock_encoding:
            mock_encoder = Mock()
            mock_encoder.encode.return_value = [1, 2, 3, 4, 5]
            mock_encoding.return_value = mock_encoder

            result = count_tokens("Hello world")
            assert result == 5
            mock_encoder.encode.assert_called_once_with("Hello world")

    def test_count_tokens_fallback(self):
        """Test token counting fallback to word count."""
        with patch("tiktoken.get_encoding", side_effect=Exception("Encoding failed")):
            result = count_tokens("Hello world test")
            assert result == 3  # Word count

    def test_is_test_or_config_file(self):
        """Test detection of test and config files."""
        assert is_test_or_config_file("/path/to/test_file.py") is True
        assert is_test_or_config_file("/path/to/tests/file.py") is True
        assert is_test_or_config_file("/path/to/myconfig.py") is True
        assert is_test_or_config_file("/path/to/setup.py") is True
        assert is_test_or_config_file("/path/to/conftest.py") is True
        assert is_test_or_config_file("/path/to/regular_file.py") is False

    def test_generate_anchor_name(self):
        """Test anchor name generation."""
        decl = Declaration(kind="function", name="test_function", start_line=10, end_line=20)

        result = _generate_anchor_name("/path/to/file.py", decl)
        assert result == "symbol-path_to_file_py-function-test_function"

    def test_write_markdown_basic(self):
        """Test basic markdown writing."""
        config = CodeConCatConfig()
        config.output = "output.md"
        config.include_repo_overview = False
        config.include_file_index = False
        config.enable_compression = False

        file_data = AnnotatedFileData(
            file_path="/test/sample.py",
            content='def hello():\n    print("Hello")',
            annotated_content='def hello():\n    print("Hello")',
            language="python",
            summary="Test file",
            declarations=[
                Declaration(
                    kind="function",
                    name="hello",
                    start_line=1,
                    end_line=2,
                ),
            ],
        )

        items = [file_data]

        with patch("codeconcat.writer.markdown_writer.print_quote_with_ascii"):
            result = write_markdown(items, config)

        # Check that result is not empty
        assert result
        assert isinstance(result, str)

    def test_write_markdown_with_ai_preamble(self):
        """Test markdown writing with AI preamble."""
        config = CodeConCatConfig()
        config.output = "output.md"
        config.disable_ai_context = False
        config.include_repo_overview = True  # Must be True for AI preamble
        config.include_file_index = False
        config.enable_compression = False
        config.include_directory_structure = False
        config.sort_files = False

        file_data = AnnotatedFileData(
            file_path="/test/sample.py",
            content="pass",
            annotated_content="pass",
            language="python",
            summary="",
            tags=[],
        )

        # Mock the render_markdown_chunks method
        file_data.render_markdown_chunks = Mock(
            return_value=["### /test/sample.py", "```python", "pass", "```"]
        )

        items = [file_data]

        with patch("codeconcat.writer.markdown_writer.print_quote_with_ascii"):
            with patch(
                "codeconcat.writer.markdown_writer.generate_ai_preamble", return_value="AI Preamble"
            ):
                result = write_markdown(items, config)

        # Check that AI preamble was included in result
        assert "AI Preamble" in result

    def test_write_markdown_empty_items(self):
        """Test writing with empty items list."""
        config = CodeConCatConfig()
        config.output = "output.md"

        with patch("codeconcat.writer.markdown_writer.print_quote_with_ascii"):
            result = write_markdown([], config)

        # Should still return content
        assert result
        assert isinstance(result, str)

    def test_write_markdown_with_folder_tree(self):
        """Test writing with folder tree."""
        config = CodeConCatConfig()
        config.output = "output.md"
        config.include_repo_overview = True
        config.include_directory_structure = True
        config.include_file_index = False

        folder_tree = "├── src/\n│   └── main.py\n└── README.md"

        with patch("codeconcat.writer.markdown_writer.print_quote_with_ascii"):
            result = write_markdown([], config, folder_tree)

        # Check that folder tree was included
        assert "Directory Structure" in result or "src/" in result
