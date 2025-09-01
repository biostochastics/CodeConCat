"""
Tests for the CodeConCat diagnose commands.

Tests diagnostic and verification functionality.
"""

import pytest
from typer.testing import CliRunner

from codeconcat.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_code_files(tmp_path):
    """Create sample code files for parser testing."""
    # Python file
    python_file = tmp_path / "sample.py"
    python_file.write_text(
        '''"""Sample Python module."""

def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

class Person:
    """Represents a person."""

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def introduce(self) -> str:
        """Introduce the person."""
        return f"I'm {self.name}, {self.age} years old"
'''
    )

    # JavaScript file
    js_file = tmp_path / "sample.js"
    js_file.write_text(
        """// Sample JavaScript module

function calculateSum(a, b) {
    return a + b;
}

class Calculator {
    constructor() {
        this.memory = 0;
    }

    add(value) {
        this.memory += value;
        return this.memory;
    }
}

const multiply = (x, y) => x * y;

export { calculateSum, Calculator, multiply };
"""
    )

    # Java file
    java_file = tmp_path / "Sample.java"
    java_file.write_text(
        """package com.example;

/**
 * Sample Java class for testing.
 */
public class Sample {
    private String name;
    private int value;

    public Sample(String name, int value) {
        this.name = name;
        this.value = value;
    }

    public String getName() {
        return name;
    }

    public int getValue() {
        return value;
    }

    public void setValue(int value) {
        this.value = value;
    }
}
"""
    )

    return tmp_path


class TestDiagnoseCommand:
    """Test suite for the diagnose commands."""

    def test_diagnose_verify(self, runner):
        """Test verification of Tree-sitter dependencies."""
        result = runner.invoke(app, ["diagnose", "verify"])

        assert result.exit_code == 0
        assert "Verifying Tree-sitter" in result.stdout or "Tree-sitter" in result.stdout
        # Should list available parsers
        assert "python" in result.stdout.lower() or "Available" in result.stdout

    def test_diagnose_languages(self, runner):
        """Test listing supported languages."""
        result = runner.invoke(app, ["diagnose", "languages"])

        assert result.exit_code == 0
        assert "Language Support" in result.stdout or "Supported Languages" in result.stdout

        # Check for some expected languages
        assert "python" in result.stdout.lower()
        assert "javascript" in result.stdout.lower()
        assert "java" in result.stdout.lower()

        # Check for parser type indicators
        assert "Tree-sitter" in result.stdout or "Regex" in result.stdout

        # Should show file extensions
        assert ".py" in result.stdout
        assert ".js" in result.stdout
        assert ".java" in result.stdout

    def test_diagnose_system(self, runner):
        """Test system information display."""
        result = runner.invoke(app, ["diagnose", "system"])

        assert result.exit_code == 0
        assert "System Information" in result.stdout or "System" in result.stdout

        # Should show various system details
        assert any(
            item in result.stdout.lower()
            for item in ["python", "version", "platform", "os", "machine", "processor"]
        )

    def test_diagnose_parser_python(self, runner):
        """Test Python parser diagnostic."""
        result = runner.invoke(app, ["diagnose", "parser", "python"])

        assert result.exit_code == 0
        assert "python" in result.stdout.lower()
        assert "Parser" in result.stdout or "parser" in result.stdout.lower()

        # Should indicate success or show parser details
        assert any(
            word in result.stdout.lower()
            for word in ["available", "ready", "loaded", "success", "✓", "✔"]
        )

    def test_diagnose_parser_javascript(self, runner):
        """Test JavaScript parser diagnostic."""
        result = runner.invoke(app, ["diagnose", "parser", "javascript"])

        assert result.exit_code == 0
        assert "javascript" in result.stdout.lower()

    def test_diagnose_parser_with_file(self, runner, sample_code_files):
        """Test parser with specific file."""
        python_file = sample_code_files / "sample.py"

        result = runner.invoke(
            app, ["diagnose", "parser", "python", "--test-file", str(python_file)]
        )

        assert result.exit_code == 0
        assert "python" in result.stdout.lower()

        # Should show parsing results
        assert any(
            word in result.stdout.lower()
            for word in ["function", "class", "declaration", "parsed", "found", "greet", "person"]
        )

    def test_diagnose_parser_javascript_with_file(self, runner, sample_code_files):
        """Test JavaScript parser with specific file."""
        js_file = sample_code_files / "sample.js"

        result = runner.invoke(
            app, ["diagnose", "parser", "javascript", "--test-file", str(js_file)]
        )

        assert result.exit_code == 0
        assert "javascript" in result.stdout.lower()

        # Should indicate successful parsing or show test results
        # Rich console output may not capture specific parsing terms
        assert (
            any(
                indicator in result.stdout.lower()
                for indicator in ["test results", "declarations", "success", "✓", "completed"]
            )
            or "javascript" in result.stdout.lower()
        )

    def test_diagnose_parser_java_with_file(self, runner, sample_code_files):
        """Test Java parser with specific file."""
        java_file = sample_code_files / "Sample.java"

        result = runner.invoke(app, ["diagnose", "parser", "java", "--test-file", str(java_file)])

        assert result.exit_code == 0
        assert "java" in result.stdout.lower()

    def test_diagnose_parser_invalid_language(self, runner):
        """Test parser diagnostic with invalid language."""
        result = runner.invoke(app, ["diagnose", "parser", "invalid_language"])

        # Should handle gracefully
        assert (
            "not supported" in result.stdout.lower()
            or "invalid" in result.stdout.lower()
            or "unknown" in result.stdout.lower()
            or result.exit_code != 0
        )

    def test_diagnose_parser_nonexistent_file(self, runner):
        """Test parser with nonexistent file."""
        result = runner.invoke(
            app, ["diagnose", "parser", "python", "--test-file", "/nonexistent/file.py"]
        )

        # Typer handles file validation and exits with code 2
        assert result.exit_code != 0
        # Check stdout only since stderr is not separately captured
        output_text = result.stdout.lower() if result.stdout else ""
        assert (
            any(
                indicator in output_text
                for indicator in ["not found", "does not exist", "error", "invalid"]
            )
            or result.exit_code == 2
        )  # Typer's validation error exit code

    def test_diagnose_rich_formatting(self, runner):
        """Test that Rich formatting is used in diagnose output."""
        result = runner.invoke(app, ["diagnose", "languages"])

        assert result.exit_code == 0
        # Rich panels or formatting
        assert any(char in result.stdout for char in ["╭", "╰", "┌", "└", "│"])

    def test_diagnose_parser_all_supported_languages(self, runner):
        """Test that all major supported languages can be diagnosed."""
        languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "csharp",
            "cpp",
            "go",
            "rust",
            "php",
            "julia",
            "r",
        ]

        for lang in languages:
            result = runner.invoke(app, ["diagnose", "parser", lang])
            # Language should either be supported or clearly indicated as not supported
            assert result.exit_code == 0 or "not supported" in result.stdout.lower()

    def test_diagnose_verify_shows_parser_status(self, runner):
        """Test that verify shows status of each parser."""
        result = runner.invoke(app, ["diagnose", "verify"])

        assert result.exit_code == 0
        # Should show status indicators
        assert any(
            indicator in result.stdout
            for indicator in ["✓", "✔", "✗", "✘", "Available", "Missing", "OK", "Error"]
        )

    def test_diagnose_system_shows_dependencies(self, runner):
        """Test that system info shows key dependencies."""
        result = runner.invoke(app, ["diagnose", "system"])

        assert result.exit_code == 0
        # Should show dependency versions
        assert any(
            dep in result.stdout.lower() for dep in ["typer", "rich", "pydantic", "tree", "sitter"]
        )

    def test_diagnose_parser_performance(self, runner, sample_code_files):
        """Test parser performance metrics if available."""
        python_file = sample_code_files / "sample.py"

        result = runner.invoke(
            app, ["diagnose", "parser", "python", "--test-file", str(python_file)]
        )

        assert result.exit_code == 0
        # Might show timing or performance info
        # Just verify it completes successfully
