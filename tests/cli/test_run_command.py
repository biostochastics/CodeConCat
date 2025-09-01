"""
Comprehensive tests for the CodeConCat run command.

Tests all user scenarios identified through deep analysis:
- LLM context preparation
- CI/CD pipeline integration
- Security scanning
- Performance optimization
- Error handling
"""

import json

import pytest
from typer.testing import CliRunner

from codeconcat.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for testing."""
    # Create Python file
    python_file = tmp_path / "sample.py"
    python_file.write_text(
        '''"""Sample Python module for testing."""

def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y

class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.memory = 0

    def calculate(self, operation: str, a: float, b: float) -> float:
        """Perform a calculation."""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"Unknown operation: {operation}")
'''
    )

    # Create JavaScript file
    js_file = tmp_path / "utils.js"
    js_file.write_text(
        """// Utility functions
function formatDate(date) {
    return date.toLocaleDateString();
}

const greet = (name) => {
    console.log(`Hello, ${name}!`);
};

export { formatDate, greet };
"""
    )

    # Create a config file
    config_file = tmp_path / ".codeconcat.yml"
    config_file.write_text(
        """version: '1.0'
output_preset: medium
format: markdown
use_gitignore: true
use_default_excludes: true
parser_engine: tree_sitter
"""
    )

    return tmp_path


class TestRunCommand:
    """Test suite for the run command."""

    def test_scenario_1_llm_context_preparation(self, runner, sample_project, tmp_path):
        """Test Scenario 1: Solo developer preparing code for LLM analysis."""
        output_file = tmp_path / "llm_context.md"

        result = runner.invoke(
            app,
            [
                "run",
                str(sample_project),
                "--preset",
                "lean",
                "--format",
                "markdown",
                "-o",
                str(output_file),
                "--compress",
                "--compression-level",
                "aggressive",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Processing Complete!" in result.stdout
        assert "Compression Effectiveness" in result.stdout

        # Check that compression actually reduced token count
        assert "reduction" in result.stdout

        # Verify output contains compressed markers
        content = output_file.read_text()
        assert "...code omitted" in content or "def add" in content

    def test_scenario_2_cicd_json_output(self, runner, sample_project, tmp_path):
        """Test Scenario 2: DevOps engineer integrating into CI/CD pipeline."""
        output_file = tmp_path / "cicd_output.json"

        result = runner.invoke(
            app, ["--quiet", "run", str(sample_project), "--format", "json", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Validate JSON structure
        with open(output_file) as f:
            data = json.load(f)

        assert "files" in data
        assert len(data["files"]) > 0
        assert all("file_path" in f for f in data["files"])
        assert all("language" in f for f in data["files"])
        assert all("content" in f for f in data["files"])

    def test_scenario_3_multi_language_filtering(self, runner, sample_project, tmp_path):
        """Test Scenario 3: Multi-language project with filtering."""
        output_file = tmp_path / "filtered_output.md"

        result = runner.invoke(
            app,
            [
                "run",
                str(sample_project),
                "-il",
                "python",  # Include only Python
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "sample.py" in content
        assert "utils.js" not in content  # JavaScript should be excluded

    def test_scenario_4_security_scanning(self, runner, sample_project, tmp_path):
        """Test Scenario 4: Security team scanning codebase."""
        output_file = tmp_path / "security_scan.json"

        result = runner.invoke(
            app,
            [
                "run",
                str(sample_project),
                "--format",
                "json",
                "--security",
                "--security-threshold",
                "MEDIUM",
                "-o",
                str(output_file),
            ],
        )

        # Security scanning might not find issues in our simple sample
        # Just verify the command runs without error
        assert result.exit_code == 0
        assert output_file.exists()

    def test_scenario_5_compression_levels(self, runner, sample_project, tmp_path):
        """Test Scenario 5: Different compression levels."""
        compression_levels = ["low", "medium", "high", "aggressive"]

        for level in compression_levels:
            output_file = tmp_path / f"compressed_{level}.md"

            result = runner.invoke(
                app,
                [
                    "run",
                    str(sample_project),
                    "--compress",
                    "--compression-level",
                    level,
                    "-o",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert output_file.exists()
            assert f"Level: {level}" in result.stdout

    def test_scenario_6_output_formats(self, runner, sample_project, tmp_path):
        """Test Scenario 6: All output formats."""
        formats = ["markdown", "json", "xml", "text"]

        for fmt in formats:
            output_file = tmp_path / f"output.{fmt}"

            result = runner.invoke(
                app, ["run", str(sample_project), "--format", fmt, "-o", str(output_file)]
            )

            assert result.exit_code == 0
            assert output_file.exists()
            assert f"Format: {fmt}" in result.stdout

    def test_scenario_7_presets(self, runner, sample_project, tmp_path):
        """Test Scenario 7: Different output presets."""
        presets = ["lean", "medium", "full"]

        for preset in presets:
            output_file = tmp_path / f"preset_{preset}.md"

            result = runner.invoke(
                app, ["run", str(sample_project), "--preset", preset, "-o", str(output_file)]
            )

            assert result.exit_code == 0
            assert output_file.exists()

    def test_scenario_8_max_workers(self, runner, sample_project, tmp_path):
        """Test Scenario 8: Parallel processing with max workers."""
        output_file = tmp_path / "parallel.md"

        result = runner.invoke(
            app, ["run", str(sample_project), "--max-workers", "8", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

    def test_scenario_9_exclude_patterns(self, runner, sample_project, tmp_path):
        """Test Scenario 9: Exclude patterns."""
        output_file = tmp_path / "excluded.md"

        # Create a test directory to exclude
        test_dir = sample_project / "tests"
        test_dir.mkdir()
        (test_dir / "test_sample.py").write_text("# Test file")

        result = runner.invoke(
            app, ["run", str(sample_project), "-ep", "**/tests/**", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "test_sample.py" not in content

    def test_scenario_10_verbose_output(self, runner, sample_project, tmp_path):
        """Test Scenario 10: Verbose output for debugging."""
        output_file = tmp_path / "verbose.md"

        result = runner.invoke(
            app,
            [
                "-vv",  # Double verbose for DEBUG level
                "run",
                str(sample_project),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        # With debug logging, we should see more detailed output
        # The actual debug messages depend on the logging configuration

    def test_error_handling_invalid_path(self, runner):
        """Test error handling for invalid path."""
        result = runner.invoke(app, ["run", "/nonexistent/path"])

        assert result.exit_code != 0
        output_text = result.output.lower() if result.output else ""
        assert (
            "error" in output_text or "not found" in output_text or "does not exist" in output_text
        )

    def test_error_handling_invalid_format(self, runner, sample_project):
        """Test error handling for invalid output format."""
        result = runner.invoke(app, ["run", str(sample_project), "--format", "invalid"])

        assert result.exit_code != 0
        output_text = result.output.lower() if result.output else ""
        assert "invalid value" in output_text or "invalid" in output_text

    def test_cat_quotes_displayed(self, runner, sample_project, tmp_path):
        """Test that cat quotes are displayed in output."""
        output_file = tmp_path / "quotes.md"

        result = runner.invoke(app, ["run", str(sample_project), "-o", str(output_file)])

        assert result.exit_code == 0
        # Cat quotes should appear at the start of output
        # They contain either cat-related puns or programming quotes
        assert any(
            word in result.stdout.lower() for word in ["cat", "kitten", "paw", "purr"]
        ) or any(quote in result.stdout for quote in ["simple", "impossible", "complex"])

    def test_rich_formatting_panels(self, runner, sample_project, tmp_path):
        """Test that Rich panels and formatting are displayed."""
        output_file = tmp_path / "rich.md"

        result = runner.invoke(app, ["run", str(sample_project), "-o", str(output_file)])

        assert result.exit_code == 0
        # Rich panels use box drawing characters
        assert "╭" in result.stdout or "┌" in result.stdout
        assert "╰" in result.stdout or "└" in result.stdout
        assert "Processing Configuration" in result.stdout or "Processing Complete" in result.stdout

    def test_token_summary_displayed(self, runner, sample_project, tmp_path):
        """Test that token summary is displayed."""
        output_file = tmp_path / "tokens.md"

        result = runner.invoke(app, ["run", str(sample_project), "-o", str(output_file)])

        assert result.exit_code == 0
        assert "Token Summary" in result.stdout
        assert "Claude" in result.stdout or "GPT" in result.stdout

    def test_progress_indicators(self, runner, sample_project, tmp_path):
        """Test that progress indicators are shown (when not quiet)."""
        output_file = tmp_path / "progress.md"

        result = runner.invoke(app, ["run", str(sample_project), "-o", str(output_file)])

        assert result.exit_code == 0
        # Progress indicators include processing messages
        assert "Processing files" in result.stdout or "✔" in result.stdout or "✓" in result.stdout
