"""Simple tests for AI context generation."""


from codeconcat.writer.ai_context import generate_ai_preamble
from codeconcat.base_types import (
    AnnotatedFileData,
    ParsedDocData,
    Declaration,
)


class TestAIContextSimple:
    """Simple test suite for AI context generation."""

    def test_generate_ai_preamble_basic(self):
        """Test basic AI preamble generation."""
        # Create simple test data
        code_file = AnnotatedFileData(
            file_path="/test/main.py",
            content='def hello():\n    print("Hello")',
            annotated_content='def hello():\n    print("Hello")',
            language="python",
            summary="Test file with hello function",
            declarations=[
                Declaration(
                    kind="function",
                    name="hello",
                    start_line=1,
                    end_line=2,
                ),
            ],
        )

        doc_file = ParsedDocData(
            file_path="/test/README.md",
            content="# Test Project",
        )

        items = [code_file, doc_file]
        result = generate_ai_preamble(items)

        # Basic checks
        assert "# AI-Friendly Code Summary" in result
        assert "Total code files: 1" in result
        assert "Documentation files: 1" in result
        assert "Total functions found: 1" in result

    def test_generate_ai_preamble_empty(self):
        """Test AI preamble with empty items."""
        result = generate_ai_preamble([])

        assert "Total code files: 0" in result
        assert "Documentation files: 0" in result
        assert "Total functions found: 0" in result

    def test_generate_ai_preamble_entry_points(self):
        """Test detection of entry points."""
        # Create entry point files
        main_file = AnnotatedFileData(
            file_path="/project/main.py",
            content="if __name__ == '__main__':",
            annotated_content="if __name__ == '__main__':",
            language="python",
        )

        app_file = AnnotatedFileData(
            file_path="/project/app.py",
            content="app = Flask(__name__)",
            annotated_content="app = Flask(__name__)",
            language="python",
        )

        items = [main_file, app_file]
        result = generate_ai_preamble(items)

        assert "- `/project/main.py`" in result
        assert "- `/project/app.py`" in result

    def test_generate_ai_preamble_file_extensions(self):
        """Test file type counting."""
        files = [
            AnnotatedFileData(
                file_path="/test/file1.py",
                content="pass",
                annotated_content="pass",
                language="python",
            ),
            AnnotatedFileData(
                file_path="/test/file2.py",
                content="pass",
                annotated_content="pass",
                language="python",
            ),
            AnnotatedFileData(
                file_path="/test/file.js",
                content="console.log('test')",
                annotated_content="console.log('test')",
                language="javascript",
            ),
        ]

        result = generate_ai_preamble(files)

        assert "- py: 2 files" in result
        assert "- js: 1 files" in result

    def test_generate_ai_preamble_with_summaries(self):
        """Test key files with summaries."""
        files = [
            AnnotatedFileData(
                file_path="/test/core.py",
                content="class Core:",
                annotated_content="class Core:",
                language="python",
                summary="Core functionality",
            ),
            AnnotatedFileData(
                file_path="/test/utils.py",
                content="def util():",
                annotated_content="def util():",
                language="python",
                summary="",  # Empty summary
            ),
        ]

        result = generate_ai_preamble(files)

        assert "- `/test/core.py`: Core functionality" in result
        assert "utils.py" not in result  # Should not show files without summaries

    def test_generate_ai_preamble_function_stats(self):
        """Test function statistics calculation."""
        files = [
            AnnotatedFileData(
                file_path="/test/file.py",
                content="def f1():\n    pass\n\ndef f2():\n    line1\n    line2",
                annotated_content="def f1():\n    pass\n\ndef f2():\n    line1\n    line2",
                language="python",
                declarations=[
                    Declaration(
                        kind="function",
                        name="f1",
                        start_line=1,
                        end_line=2,
                    ),
                    Declaration(
                        kind="function",
                        name="f2",
                        start_line=4,
                        end_line=6,
                    ),
                    Declaration(
                        kind="class",
                        name="MyClass",
                        start_line=8,
                        end_line=10,
                    ),
                ],
            ),
        ]

        result = generate_ai_preamble(files)

        # Should count only functions, not classes
        assert "Total functions found: 2" in result
        # Average: (2 + 3) / 2 = 2.5
        assert "Average function length: 2.5 lines" in result
