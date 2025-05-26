"""Tests for the doc_extractor module."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from codeconcat.base_types import CodeConCatConfig, ParsedDocData
from codeconcat.parser.doc_extractor import (
    extract_docs,
    is_doc_file,
    parse_doc_file,
    read_doc_content,
)


class TestDocExtractor:
    """Test suite for document extraction functionality."""

    def test_is_doc_file_with_matching_extension(self):
        """Test is_doc_file returns True for matching extensions."""
        assert is_doc_file("readme.md", [".md", ".txt"]) is True
        assert is_doc_file("doc.txt", [".md", ".txt"]) is True
        assert is_doc_file("FILE.MD", [".md", ".txt"]) is True  # Case insensitive

    def test_is_doc_file_with_non_matching_extension(self):
        """Test is_doc_file returns False for non-matching extensions."""
        assert is_doc_file("script.py", [".md", ".txt"]) is False
        assert is_doc_file("code.js", [".md", ".txt"]) is False
        assert is_doc_file("noext", [".md", ".txt"]) is False

    def test_read_doc_content_success(self):
        """Test read_doc_content successfully reads file content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write("# Test Document\nThis is content.")
            tmp_path = tmp.name

        try:
            content = read_doc_content(tmp_path)
            assert content == "# Test Document\nThis is content."
        finally:
            os.unlink(tmp_path)

    def test_read_doc_content_file_not_found(self):
        """Test read_doc_content returns empty string on error."""
        content = read_doc_content("/nonexistent/file.md")
        assert content == ""

    def test_read_doc_content_with_encoding_errors(self):
        """Test read_doc_content handles encoding errors gracefully."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as tmp:
            # Write some invalid UTF-8
            tmp.write(b"Valid text \xff\xfe Invalid bytes")
            tmp_path = tmp.name

        try:
            content = read_doc_content(tmp_path)
            # Should handle the error and still return content
            assert "Valid text" in content
        finally:
            os.unlink(tmp_path)

    def test_parse_doc_file(self):
        """Test parse_doc_file creates ParsedDocData correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write("# Documentation\nContent here.")
            tmp_path = tmp.name

        try:
            result = parse_doc_file(tmp_path)
            assert isinstance(result, ParsedDocData)
            assert result.file_path == tmp_path
            assert result.doc_type == "md"
            assert result.content == "# Documentation\nContent here."
        finally:
            os.unlink(tmp_path)

    def test_parse_doc_file_different_extensions(self):
        """Test parse_doc_file handles different extensions correctly."""
        extensions = [".txt", ".rst", ".adoc"]

        for ext in extensions:
            with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as tmp:
                tmp.write("Content")
                tmp_path = tmp.name

            try:
                result = parse_doc_file(tmp_path)
                assert result.doc_type == ext.lstrip(".")
            finally:
                os.unlink(tmp_path)

    def test_extract_docs_filters_by_extension(self):
        """Test extract_docs only processes files with doc extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            doc_file = os.path.join(tmpdir, "readme.md")
            with open(doc_file, "w") as f:
                f.write("# README")

            code_file = os.path.join(tmpdir, "script.py")
            with open(code_file, "w") as f:
                f.write("print('hello')")

            txt_file = os.path.join(tmpdir, "notes.txt")
            with open(txt_file, "w") as f:
                f.write("Notes")

            # Create config
            config = MagicMock(spec=CodeConCatConfig)
            config.doc_extensions = [".md", ".txt"]
            config.max_workers = 2

            # Extract docs
            file_paths = [doc_file, code_file, txt_file]
            results = extract_docs(file_paths, config)

            # Should process .md and .txt files only
            assert len(results) == 2
            result_paths = [r.file_path for r in results]
            assert doc_file in result_paths
            assert txt_file in result_paths
            assert code_file not in result_paths

    def test_extract_docs_parallel_processing(self):
        """Test extract_docs processes files in parallel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple doc files
            doc_files = []
            for i in range(5):
                path = os.path.join(tmpdir, f"doc{i}.md")
                with open(path, "w") as f:
                    f.write(f"Document {i}")
                doc_files.append(path)

            # Create config
            config = MagicMock(spec=CodeConCatConfig)
            config.doc_extensions = [".md"]
            config.max_workers = 3

            # Extract docs
            results = extract_docs(doc_files, config)

            # All files should be processed
            assert len(results) == 5
            for i, result in enumerate(sorted(results, key=lambda r: r.file_path)):
                assert f"Document {i}" in result.content

    def test_extract_docs_empty_list(self):
        """Test extract_docs handles empty file list."""
        config = MagicMock(spec=CodeConCatConfig)
        config.doc_extensions = [".md"]
        config.max_workers = 2

        results = extract_docs([], config)
        assert results == []

    def test_extract_docs_no_matching_files(self):
        """Test extract_docs when no files match doc extensions."""
        config = MagicMock(spec=CodeConCatConfig)
        config.doc_extensions = [".md"]
        config.max_workers = 2

        results = extract_docs(["/path/to/file.py", "/path/to/file.js"], config)
        assert results == []

    @patch("codeconcat.parser.doc_extractor.ThreadPoolExecutor")
    def test_extract_docs_uses_thread_pool(self, mock_executor_class):
        """Test extract_docs uses ThreadPoolExecutor correctly."""
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        mock_executor.map.return_value = []

        config = MagicMock(spec=CodeConCatConfig)
        config.doc_extensions = [".md"]
        config.max_workers = 4

        extract_docs(["/path/doc.md"], config)

        # Verify ThreadPoolExecutor was created with correct max_workers
        mock_executor_class.assert_called_once_with(max_workers=4)
        mock_executor.map.assert_called_once()
