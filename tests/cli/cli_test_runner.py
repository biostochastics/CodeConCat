"""
CLI Test Runner - Utilities for running and validating CLI tests.

This module provides helper functions and fixtures for testing the CodeConCat CLI.
"""

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

from typer.testing import CliRunner

from codeconcat.cli import app


class CLITestRunner:
    """Enhanced CLI test runner with validation helpers."""

    def __init__(self):
        self.runner = CliRunner()
        self.temp_dirs: list[Path] = []

    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()

    @contextmanager
    def temp_project(self, name: str = "test_project"):
        """Create a temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix=f"codeconcat_{name}_"))
        self.temp_dirs.append(temp_dir)
        try:
            yield temp_dir
        finally:
            pass  # Cleanup happens in cleanup() method

    def run_command(
        self,
        args: list[str],
        input_text: str | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[int, str, str]:
        """
        Run a CLI command and return exit code, stdout, and stderr.

        Args:
            args: Command arguments
            input_text: Optional input to provide to the command
            env: Optional environment variables

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        result = self.runner.invoke(app, args, input=input_text, env=env)
        return result.exit_code, result.stdout, result.stderr or ""

    def run_and_validate(
        self,
        args: list[str],
        expected_exit_code: int = 0,
        expected_in_stdout: list[str] | None = None,
        not_expected_in_stdout: list[str] | None = None,
    ) -> bool:
        """
        Run a command and validate the output.

        Args:
            args: Command arguments
            expected_exit_code: Expected exit code
            expected_in_stdout: Strings that should appear in stdout
            not_expected_in_stdout: Strings that should not appear in stdout

        Returns:
            True if all validations pass
        """
        exit_code, stdout, stderr = self.run_command(args)

        if exit_code != expected_exit_code:
            print(f"Exit code mismatch: expected {expected_exit_code}, got {exit_code}")
            print(f"Stdout: {stdout}")
            print(f"Stderr: {stderr}")
            return False

        if expected_in_stdout:
            for expected in expected_in_stdout:
                if expected not in stdout:
                    print(f"Expected '{expected}' not found in stdout")
                    print(f"Stdout: {stdout}")
                    return False

        if not_expected_in_stdout:
            for not_expected in not_expected_in_stdout:
                if not_expected in stdout:
                    print(f"Unexpected '{not_expected}' found in stdout")
                    print(f"Stdout: {stdout}")
                    return False

        return True

    def create_sample_project(
        self,
        project_dir: Path,
        languages: list[str] = None,
        include_tests: bool = True,
        include_docs: bool = True,
    ) -> dict[str, Path]:
        """
        Create a sample project structure for testing.

        Args:
            project_dir: Directory to create the project in
            languages: List of languages to include (python, javascript, java, etc.)
            include_tests: Whether to include test files
            include_docs: Whether to include documentation

        Returns:
            Dictionary mapping file types to their paths
        """
        if languages is None:
            languages = ["python", "javascript"]

        files = {}

        # Create source directory
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        if "python" in languages:
            # Python files
            py_file = src_dir / "main.py"
            py_file.write_text(
                '''"""Main Python module."""

def main():
    """Main entry point."""
    print("Hello from Python!")
    return 0

class Application:
    """Application class."""

    def __init__(self, name: str):
        self.name = name

    def run(self):
        """Run the application."""
        print(f"Running {self.name}")

if __name__ == "__main__":
    main()
'''
            )
            files["python_main"] = py_file

        if "javascript" in languages:
            # JavaScript files
            js_file = src_dir / "app.js"
            js_file.write_text(
                """// Main JavaScript application

function main() {
    console.log("Hello from JavaScript!");
    return 0;
}

class Application {
    constructor(name) {
        this.name = name;
    }

    run() {
        console.log(`Running ${this.name}`);
    }
}

module.exports = { main, Application };
"""
            )
            files["javascript_main"] = js_file

        if "java" in languages:
            # Java files
            java_file = src_dir / "Application.java"
            java_file.write_text(
                """package com.example;

/**
 * Main application class.
 */
public class Application {
    private String name;

    public Application(String name) {
        this.name = name;
    }

    public void run() {
        System.out.println("Running " + name);
    }

    public static void main(String[] args) {
        Application app = new Application("TestApp");
        app.run();
    }
}
"""
            )
            files["java_main"] = java_file

        if include_tests:
            # Test directory
            test_dir = project_dir / "tests"
            test_dir.mkdir(exist_ok=True)

            test_file = test_dir / "test_main.py"
            test_file.write_text(
                '''"""Test file."""

def test_example():
    """Example test."""
    assert 1 + 1 == 2
'''
            )
            files["test"] = test_file

        if include_docs:
            # Documentation
            readme = project_dir / "README.md"
            readme.write_text(
                """# Test Project

This is a test project for CodeConCat CLI testing.

## Features

- Multiple language support
- Test coverage
- Documentation

## Usage

Run the main application to get started.
"""
            )
            files["readme"] = readme

        # Configuration files
        gitignore = project_dir / ".gitignore"
        gitignore.write_text(
            """*.pyc
__pycache__/
node_modules/
*.class
.venv/
venv/
"""
        )
        files["gitignore"] = gitignore

        return files

    def validate_json_output(self, json_file: Path) -> bool:
        """
        Validate that a JSON output file has the expected structure.

        Args:
            json_file: Path to the JSON file

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(json_file) as f:
                data = json.load(f)

            # Check required fields
            if "files" not in data:
                print("Missing 'files' field in JSON")
                return False

            # Check file structure
            for file_entry in data["files"]:
                required_fields = ["file_path", "language", "content"]
                for field in required_fields:
                    if field not in file_entry:
                        print(f"Missing '{field}' field in file entry")
                        return False

            return True
        except Exception as e:
            print(f"Error validating JSON: {e}")
            return False

    def validate_markdown_output(self, md_file: Path) -> bool:
        """
        Validate that a Markdown output file has expected content.

        Args:
            md_file: Path to the Markdown file

        Returns:
            True if valid, False otherwise
        """
        try:
            content = md_file.read_text()

            # Check for expected sections
            if "# CodeConCat Output" not in content and "## Files" not in content:
                print("Missing expected Markdown headers")
                return False

            # Check for code blocks
            if "```" not in content:
                print("No code blocks found in Markdown")
                return False

            return True
        except Exception as e:
            print(f"Error validating Markdown: {e}")
            return False

    def measure_compression_ratio(self, project_dir: Path, compression_level: str) -> float:
        """
        Measure the compression ratio for a given compression level.

        Args:
            project_dir: Directory to process
            compression_level: Compression level to use

        Returns:
            Compression ratio (0.0 to 1.0)
        """
        with tempfile.NamedTemporaryFile(suffix=".md") as f:
            output_file = Path(f.name)

            # Run without compression
            exit_code1, stdout1, _ = self.run_command(
                ["--quiet", "run", str(project_dir), "-o", str(output_file)]
            )

            if exit_code1 != 0:
                return 0.0

            uncompressed_size = output_file.stat().st_size

            # Run with compression
            exit_code2, stdout2, _ = self.run_command(
                [
                    "--quiet",
                    "run",
                    str(project_dir),
                    "--compress",
                    "--compression-level",
                    compression_level,
                    "-o",
                    str(output_file),
                ]
            )

            if exit_code2 != 0:
                return 0.0

            compressed_size = output_file.stat().st_size

            if uncompressed_size == 0:
                return 0.0

            return 1.0 - (compressed_size / uncompressed_size)

    def test_all_formats(self, project_dir: Path) -> dict[str, bool]:
        """
        Test all output formats and return validation results.

        Args:
            project_dir: Directory to process

        Returns:
            Dictionary mapping format names to validation results
        """
        results = {}
        formats = ["markdown", "json", "xml", "text"]

        for fmt in formats:
            with tempfile.NamedTemporaryFile(suffix=f".{fmt}") as f:
                output_file = Path(f.name)

                exit_code, stdout, _ = self.run_command(
                    ["--quiet", "run", str(project_dir), "--format", fmt, "-o", str(output_file)]
                )

                if exit_code != 0:
                    results[fmt] = False
                    continue

                # Validate based on format
                if fmt == "json":
                    results[fmt] = self.validate_json_output(output_file)
                elif fmt == "markdown":
                    results[fmt] = self.validate_markdown_output(output_file)
                else:
                    # For XML and text, just check file exists and has content
                    results[fmt] = output_file.exists() and output_file.stat().st_size > 0

        return results


# Performance benchmarking utilities
class PerformanceBenchmark:
    """Utilities for performance benchmarking."""

    @staticmethod
    def measure_processing_time(runner: CLITestRunner, project_dir: Path) -> float:
        """Measure processing time for a project."""
        import time

        start_time = time.time()

        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            exit_code, _, _ = runner.run_command(["--quiet", "run", str(project_dir), "-o", f.name])

            if exit_code != 0:
                return -1.0

        return time.time() - start_time

    @staticmethod
    def measure_memory_usage(runner: CLITestRunner, project_dir: Path) -> int:
        """
        Measure peak memory usage during processing.

        Note: This is a simplified version. Real memory profiling would
        require more sophisticated tools like memory_profiler.
        """
        import resource

        # Get initial memory usage
        initial_usage = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss

        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            runner.run_command(["--quiet", "run", str(project_dir), "-o", f.name])

        # Get peak memory usage
        peak_usage = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss

        # Return difference in KB (on Linux) or bytes (on macOS)
        return peak_usage - initial_usage
