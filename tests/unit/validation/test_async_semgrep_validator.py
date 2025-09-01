"""
Comprehensive unit tests for the AsyncSemgrepValidator module.

This test suite covers all methods, error conditions, and edge cases
of the async semgrep validation functionality.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from codeconcat.errors import ValidationError
from codeconcat.validation.async_semgrep_validator import AsyncSemgrepValidator


class TestAsyncSemgrepValidator:
    """Test suite for the AsyncSemgrepValidator class."""

    @pytest.fixture
    def mock_validate_safe_path(self):
        """Mock the validate_safe_path function that's imported."""
        with patch("codeconcat.validation.async_semgrep_validator.validate_safe_path") as mock:
            mock.side_effect = lambda path: Path(path)  # Return Path object
            yield mock

    @pytest.fixture
    def mock_shutil_which_found(self):
        """Mock shutil.which to return semgrep path."""
        with patch("shutil.which", return_value="/usr/bin/semgrep") as mock:
            yield mock

    @pytest.fixture
    def mock_shutil_which_not_found(self):
        """Mock shutil.which to return None (semgrep not found)."""
        with patch("shutil.which", return_value=None) as mock:
            yield mock

    @pytest.fixture
    def sample_semgrep_results(self):
        """Sample semgrep scan results."""
        return {
            "results": [
                {
                    "check_id": "security.dangerous-eval",
                    "path": "/test/file.py",
                    "start": {"line": 10, "col": 5},
                    "end": {"line": 10, "col": 15},
                    "extra": {
                        "message": "Dangerous use of eval() function",
                        "severity": "HIGH",
                        "lines": "eval(user_input)",
                    },
                },
                {
                    "check_id": "security.hardcoded-password",
                    "path": "/test/file.py",
                    "start": {"line": 5, "col": 1},
                    "end": {"line": 5, "col": 20},
                    "extra": {
                        "message": "Hardcoded password detected",
                        "severity": "MEDIUM",
                        "lines": 'password = "secret123"',
                    },
                },
            ]
        }

    @pytest.fixture
    def empty_semgrep_results(self):
        """Empty semgrep scan results."""
        return {"results": []}

    # ============================================================================
    # Initialization Tests
    # ============================================================================

    def test_init_with_semgrep_available(self, _mock_shutil_which_found):
        """Test initialization when semgrep is available."""
        validator = AsyncSemgrepValidator()

        assert validator.semgrep_path == "/usr/bin/semgrep"
        assert validator.ruleset_path is not None
        assert validator.is_available() is True

    def test_init_with_semgrep_not_available(self, _mock_shutil_which_not_found):
        """Test initialization when semgrep is not available."""
        validator = AsyncSemgrepValidator()

        assert validator.semgrep_path is None
        assert validator.is_available() is False

    def test_init_with_custom_ruleset(self, _mock_shutil_which_found):
        """Test initialization with custom ruleset path."""
        custom_ruleset = "/custom/rules"
        validator = AsyncSemgrepValidator(ruleset_path=custom_ruleset)

        assert validator.semgrep_path == "/usr/bin/semgrep"
        assert validator.ruleset_path == custom_ruleset

    @patch("codeconcat.validation.async_semgrep_validator.Path")
    def test_get_default_ruleset_path_bundled_exists(
        self, mock_path_class, _mock_shutil_which_found
    ):
        """Test getting default ruleset when bundled ruleset exists."""
        # Mock the path to the bundled ruleset
        mock_bundled_path = MagicMock()
        mock_bundled_path.exists.return_value = True
        mock_path_class.return_value.parent.__truediv__.return_value.__truediv__.return_value = (
            mock_bundled_path
        )

        validator = AsyncSemgrepValidator()
        result = validator._get_default_ruleset_path()

        assert result == str(mock_bundled_path)

    @patch("codeconcat.validation.async_semgrep_validator.Path")
    def test_get_default_ruleset_path_bundled_not_exists(
        self, mock_path_class, _mock_shutil_which_found
    ):
        """Test getting default ruleset when bundled ruleset doesn't exist."""
        # Mock the path to the bundled ruleset not existing
        mock_bundled_path = MagicMock()
        mock_bundled_path.exists.return_value = False
        mock_path_class.return_value.parent.__truediv__.return_value.__truediv__.return_value = (
            mock_bundled_path
        )

        validator = AsyncSemgrepValidator()
        result = validator._get_default_ruleset_path()

        assert result == "https://github.com/apiiro/malicious-code-ruleset"

    # ============================================================================
    # scan_file Tests - Basic Functionality
    # ============================================================================

    @pytest.mark.asyncio
    async def test_scan_file_semgrep_not_available(
        self, _mock_shutil_which_not_found, _mock_validate_safe_path
    ):
        """Test scanning file when semgrep is not available."""
        validator = AsyncSemgrepValidator()

        with pytest.raises(ValidationError, match="Semgrep is not installed"):
            await validator.scan_file("/test/file.py")

    @pytest.mark.asyncio
    async def test_scan_file_nonexistent_file(
        self, _mock_shutil_which_found, _mock_validate_safe_path
    ):
        """Test scanning a file that doesn't exist."""
        _mock_validate_safe_path.side_effect = lambda path: Path(path)

        validator = AsyncSemgrepValidator()

        with patch("pathlib.Path.exists", return_value=False), pytest.raises(
            ValidationError, match="File does not exist"
        ):
            await validator.scan_file("/nonexistent/file.py")

    @pytest.mark.asyncio
    async def test_scan_file_successful_with_findings(
        self, _mock_shutil_which_found, _mock_validate_safe_path, sample_semgrep_results, tmp_path
    ):
        """Test successful file scan with findings."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("eval(user_input)")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 1  # Exit code 1 means findings found
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()

        # Mock results file
        results_content = json.dumps(sample_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as _mock_subprocess, patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ):
            findings = await validator.scan_file(test_file)

        assert len(findings) == 2
        assert findings[0]["type"] == "semgrep"
        assert findings[0]["rule_id"] == "security.dangerous-eval"
        assert findings[0]["message"] == "Dangerous use of eval() function"
        assert findings[0]["severity"] == "HIGH"
        assert findings[0]["line"] == 10
        assert findings[0]["column"] == 5

        assert findings[1]["rule_id"] == "security.hardcoded-password"
        assert findings[1]["severity"] == "MEDIUM"

    @pytest.mark.asyncio
    async def test_scan_file_no_findings(
        self, _mock_shutil_which_found, _mock_validate_safe_path, empty_semgrep_results, tmp_path
    ):
        """Test file scan with no findings."""
        test_file = tmp_path / "clean.py"
        test_file.write_text("print('hello world')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0  # No findings

        results_content = json.dumps(empty_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ):
            findings = await validator.scan_file(test_file)

        assert findings == []

    @pytest.mark.asyncio
    async def test_scan_file_unknown_language_skipped(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test scanning file with unknown language is skipped."""
        test_file = tmp_path / "unknown.xyz"
        test_file.write_text("some unknown content")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value=None):
            findings = await validator.scan_file(test_file)

        assert findings == []

    # ============================================================================
    # scan_file Tests - Error Conditions
    # ============================================================================

    @pytest.mark.asyncio
    async def test_scan_file_timeout(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test scan file timeout handling."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, side_effect=asyncio.TimeoutError
        ), patch(
            "codeconcat.parser.file_parser.determine_language", return_value="python"
        ), pytest.raises(ValidationError, match="Semgrep scan timed out after 120 seconds"):
            await validator.scan_file(test_file)

        # Verify process was killed
        mock_process.kill.assert_called_once()
        mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_file_semgrep_error(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test semgrep command error handling."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error: Invalid configuration")
        mock_process.returncode = 2  # Error exit code

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"", b"Error: Invalid configuration")
        ), patch(
            "codeconcat.parser.file_parser.determine_language", return_value="python"
        ), pytest.raises(ValidationError, match="Semgrep scan failed"):
            await validator.scan_file(test_file)

    @pytest.mark.asyncio
    async def test_scan_file_generic_exception(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test generic exception handling during scan."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        validator = AsyncSemgrepValidator()

        with patch(
            "asyncio.create_subprocess_exec", side_effect=OSError("Permission denied")
        ), patch(
            "codeconcat.parser.file_parser.determine_language", return_value="python"
        ), pytest.raises(ValidationError, match="Failed to scan file with semgrep"):
            await validator.scan_file(test_file)

    @pytest.mark.asyncio
    async def test_scan_file_results_file_not_found(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test when semgrep results file is not created."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        validator = AsyncSemgrepValidator()

        _original_exists = Path.exists

        def mock_exists(self):
            # Return True for the input file, False for results.json
            return not str(self).endswith("results.json")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch.object(Path, "exists", new=mock_exists), patch(
            "codeconcat.parser.file_parser.determine_language", return_value="python"
        ):
            findings = await validator.scan_file(test_file)

        assert findings == []

    # ============================================================================
    # scan_file Tests - Language Detection and Configuration
    # ============================================================================

    @pytest.mark.asyncio
    async def test_scan_file_with_explicit_language(
        self, _mock_shutil_which_found, _mock_validate_safe_path, empty_semgrep_results, tmp_path
    ):
        """Test scanning file with explicitly provided language."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("some content")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        results_content = json.dumps(empty_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_subprocess, patch("asyncio.wait_for", return_value=(b"", b"")), patch(
            "pathlib.Path.exists", return_value=True
        ), patch("builtins.open", mock_open(read_data=results_content)):
            findings = await validator.scan_file(test_file, language="python")

        # Verify language was passed to semgrep command
        args, kwargs = mock_subprocess.call_args
        # args contains all the individual command arguments passed to *cmd
        cmd_args = list(args) if args else []
        assert "--lang" in cmd_args
        assert "python" in cmd_args
        assert findings == []

    @pytest.mark.asyncio
    async def test_scan_file_with_custom_rules(
        self, _mock_shutil_which_found, _mock_validate_safe_path, empty_semgrep_results, tmp_path
    ):
        """Test scanning file when custom rules exist."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        results_content = json.dumps(empty_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_subprocess, patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ):
            await validator.scan_file(test_file)

        # Verify custom rules were included
        args, kwargs = mock_subprocess.call_args
        cmd_args = list(args) if args else []
        custom_rules_included = any("custom_security_rules.yaml" in str(arg) for arg in cmd_args)
        assert custom_rules_included

    # ============================================================================
    # scan_directory Tests - Basic Functionality
    # ============================================================================

    @pytest.mark.asyncio
    async def test_scan_directory_semgrep_not_available(
        self, _mock_shutil_which_not_found, _mock_validate_safe_path
    ):
        """Test scanning directory when semgrep is not available."""
        validator = AsyncSemgrepValidator()

        result = await validator.scan_directory("/test/dir")
        assert result == {}

    @pytest.mark.asyncio
    async def test_scan_directory_nonexistent(
        self, _mock_shutil_which_found, _mock_validate_safe_path
    ):
        """Test scanning a directory that doesn't exist."""
        _mock_validate_safe_path.side_effect = lambda path: Path(path)

        validator = AsyncSemgrepValidator()

        with patch("pathlib.Path.exists", return_value=False), pytest.raises(
            ValidationError, match="Directory does not exist"
        ):
            await validator.scan_directory("/nonexistent/dir")

    @pytest.mark.asyncio
    async def test_scan_directory_not_directory(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test scanning a path that is not a directory."""
        # Create a file instead of directory
        test_file = tmp_path / "notdir.txt"
        test_file.write_text("content")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        validator = AsyncSemgrepValidator()

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_dir", return_value=False
        ), pytest.raises(ValidationError, match="Directory does not exist"):
            await validator.scan_directory(test_file)

    @pytest.mark.asyncio
    async def test_scan_directory_successful_with_findings(
        self, _mock_shutil_which_found, _mock_validate_safe_path, sample_semgrep_results, tmp_path
    ):
        """Test successful directory scan with findings."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        _mock_validate_safe_path.side_effect = lambda _path: test_dir

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 1  # Findings found

        results_content = json.dumps(sample_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_dir", return_value=True
        ), patch("builtins.open", mock_open(read_data=results_content)):
            findings = await validator.scan_directory(test_dir)

        assert "/test/file.py" in findings
        assert len(findings["/test/file.py"]) == 2
        assert findings["/test/file.py"][0]["type"] == "semgrep"
        assert findings["/test/file.py"][0]["rule_id"] == "security.dangerous-eval"

    @pytest.mark.asyncio
    async def test_scan_directory_with_languages_filter(
        self, _mock_shutil_which_found, _mock_validate_safe_path, empty_semgrep_results, tmp_path
    ):
        """Test scanning directory with language filter."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        _mock_validate_safe_path.side_effect = lambda _path: test_dir

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        results_content = json.dumps(empty_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_subprocess, patch("asyncio.wait_for", return_value=(b"", b"")), patch(
            "pathlib.Path.exists", return_value=True
        ), patch("pathlib.Path.is_dir", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ):
            await validator.scan_directory(test_dir, languages=["python", "javascript"])

        # Verify languages were passed to semgrep
        args, kwargs = mock_subprocess.call_args
        cmd_args = list(args) if args else []
        assert "--lang" in cmd_args
        lang_indices = [i for i, arg in enumerate(cmd_args) if arg == "--lang"]
        assert len(lang_indices) == 2  # Two language filters
        assert cmd_args[lang_indices[0] + 1] == "python"
        assert cmd_args[lang_indices[1] + 1] == "javascript"

    # ============================================================================
    # scan_directory Tests - Error Conditions
    # ============================================================================

    @pytest.mark.asyncio
    async def test_scan_directory_timeout(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test directory scan timeout handling."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        _mock_validate_safe_path.side_effect = lambda _path: test_dir

        mock_process = AsyncMock()
        mock_process.kill = AsyncMock()
        mock_process.wait = AsyncMock()

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, side_effect=asyncio.TimeoutError
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_dir", return_value=True
        ), pytest.raises(ValidationError, match="Semgrep scan timed out after 300 seconds"):
            await validator.scan_directory(test_dir)

    @pytest.mark.asyncio
    async def test_scan_directory_semgrep_error(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test directory scan semgrep error handling."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        _mock_validate_safe_path.side_effect = lambda _path: test_dir

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Configuration error")
        mock_process.returncode = 2  # Error exit code

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", return_value=(b"", b"Configuration error")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.is_dir", return_value=True
        ), pytest.raises(ValidationError, match="Semgrep scan failed"):
            await validator.scan_directory(test_dir)

    @pytest.mark.asyncio
    async def test_scan_directory_no_results_file(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test directory scan when results file is not created."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        _mock_validate_safe_path.side_effect = lambda _path: test_dir

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        validator = AsyncSemgrepValidator()

        def mock_exists(self):
            # Return True for directory, False for results.json
            return not str(self).endswith("results.json")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch.object(Path, "exists", new=mock_exists), patch(
            "pathlib.Path.is_dir", return_value=True
        ):
            findings = await validator.scan_directory(test_dir)

        assert findings == {}

    # ============================================================================
    # _detect_language Tests
    # ============================================================================

    def test_detect_language_python(self, _mock_shutil_which_found):
        """Test language detection for Python files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="python"):
            result = validator._detect_language(Path("test.py"))
            assert result == "python"

    def test_detect_language_javascript(self, _mock_shutil_which_found):
        """Test language detection for JavaScript files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="javascript"):
            result = validator._detect_language(Path("test.js"))
            assert result == "js"

    def test_detect_language_typescript(self, _mock_shutil_which_found):
        """Test language detection for TypeScript files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="typescript"):
            result = validator._detect_language(Path("test.ts"))
            assert result == "ts"

    def test_detect_language_java(self, _mock_shutil_which_found):
        """Test language detection for Java files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="java"):
            result = validator._detect_language(Path("Test.java"))
            assert result == "java"

    def test_detect_language_go(self, _mock_shutil_which_found):
        """Test language detection for Go files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="go"):
            result = validator._detect_language(Path("main.go"))
            assert result == "go"

    def test_detect_language_cpp(self, _mock_shutil_which_found):
        """Test language detection for C++ files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="cpp"):
            result = validator._detect_language(Path("test.cpp"))
            assert result == "cpp"

    def test_detect_language_csharp(self, _mock_shutil_which_found):
        """Test language detection for C# files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="csharp"):
            result = validator._detect_language(Path("Test.cs"))
            assert result == "csharp"

    def test_detect_language_unsupported(self, _mock_shutil_which_found):
        """Test language detection for unsupported languages."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value="fortran"):
            result = validator._detect_language(Path("test.f90"))
            assert result is None

    def test_detect_language_unknown(self, _mock_shutil_which_found):
        """Test language detection for unknown files."""
        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value=None):
            result = validator._detect_language(Path("test.unknown"))
            assert result is None

    def test_detect_language_all_supported_mappings(self, _mock_shutil_which_found):
        """Test all supported language mappings."""
        validator = AsyncSemgrepValidator()

        mappings = {
            "python": "python",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "go": "go",
            "ruby": "ruby",
            "php": "php",
            "c": "c",
            "cpp": "cpp",
            "csharp": "csharp",
            "scala": "scala",
            "kotlin": "kotlin",
            "rust": "rust",
        }

        for codeconcat_lang, semgrep_lang in mappings.items():
            with patch(
                "codeconcat.parser.file_parser.determine_language", return_value=codeconcat_lang
            ):
                result = validator._detect_language(Path(f"test.{codeconcat_lang}"))
                assert result == semgrep_lang, f"Failed for {codeconcat_lang} -> {semgrep_lang}"

    # ============================================================================
    # Edge Cases and Integration Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_scan_file_malformed_json_results(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test handling malformed JSON in results file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        malformed_json = '{"results": [{'  # Incomplete JSON

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=malformed_json)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ), pytest.raises(ValidationError, match="Failed to scan file with semgrep"):
            await validator.scan_file(test_file)

    @pytest.mark.asyncio
    async def test_scan_file_results_missing_fields(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test handling results with missing fields."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 1

        # Results with missing fields
        partial_results = {
            "results": [
                {
                    "check_id": "test-rule",
                    # Missing path, start, end, extra
                },
                {
                    # Missing most fields
                    "extra": {"message": "Test message"}
                },
            ]
        }

        results_content = json.dumps(partial_results)

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ):
            findings = await validator.scan_file(test_file)

        # Should handle missing fields gracefully with defaults
        assert len(findings) == 2
        assert findings[0]["rule_id"] == "test-rule"
        assert findings[0]["message"] == "Unknown issue"  # Default message
        assert findings[0]["line"] == 0  # Default line
        assert findings[1]["rule_id"] == "unknown"  # Default rule_id

    @pytest.mark.asyncio
    async def test_concurrent_scans(
        self, _mock_shutil_which_found, _mock_validate_safe_path, empty_semgrep_results, tmp_path
    ):
        """Test concurrent file scanning."""
        # Create multiple test files
        test_files = []
        for i in range(5):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"print('test {i}')")
            test_files.append(test_file)

        _mock_validate_safe_path.side_effect = lambda path: Path(path)

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        results_content = json.dumps(empty_semgrep_results)

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ):
            # Run scans concurrently
            tasks = [validator.scan_file(test_file) for test_file in test_files]
            results = await asyncio.gather(*tasks)

        # All scans should complete successfully
        assert len(results) == 5
        for result in results:
            assert result == []

    @pytest.mark.asyncio
    async def test_path_security_validation_called(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test that path security validation is called."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        # Set up the mock to track calls
        _mock_validate_safe_path.side_effect = lambda _path: test_file

        validator = AsyncSemgrepValidator()

        with patch("codeconcat.parser.file_parser.determine_language", return_value=None):
            await validator.scan_file(str(test_file))

        # Verify path validation was called
        _mock_validate_safe_path.assert_called_once_with(str(test_file))

    def test_singleton_instance_created(self):
        """Test that singleton instance is created."""
        from codeconcat.validation.async_semgrep_validator import async_semgrep_validator

        assert async_semgrep_validator is not None
        assert isinstance(async_semgrep_validator, AsyncSemgrepValidator)

    @pytest.mark.asyncio
    async def test_memory_cleanup_after_scan(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test that temporary resources are cleaned up after scan."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        validator = AsyncSemgrepValidator()

        def mock_exists(self):
            # Return True for input file, False for results.json
            return not str(self).endswith("results.json")

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch.object(Path, "exists", new=mock_exists), patch(
            "codeconcat.parser.file_parser.determine_language", return_value="python"
        ), patch("tempfile.TemporaryDirectory") as mock_tempdir:
            mock_tempdir.return_value.__enter__.return_value = "/tmp/test_dir"

            await validator.scan_file(test_file)

            # Verify temporary directory context manager was used
            mock_tempdir.assert_called_once()

    # ============================================================================
    # Performance and Stress Tests
    # ============================================================================

    @pytest.mark.asyncio
    async def test_large_results_handling(
        self, _mock_shutil_which_found, _mock_validate_safe_path, tmp_path
    ):
        """Test handling large number of scan results."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        _mock_validate_safe_path.side_effect = lambda _path: test_file

        # Create large results set
        large_results = {
            "results": [
                {
                    "check_id": f"rule-{i}",
                    "path": str(test_file),
                    "start": {"line": i, "col": 1},
                    "end": {"line": i, "col": 10},
                    "extra": {
                        "message": f"Finding {i}",
                        "severity": "LOW",
                        "lines": f"line {i} content",
                    },
                }
                for i in range(1000)  # 1000 findings
            ]
        }

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 1

        results_content = json.dumps(large_results)

        validator = AsyncSemgrepValidator()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process), patch(
            "asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"")
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=results_content)
        ), patch(
            "codeconcat.parser.file_parser.determine_language",
            return_value="python",
        ):
            findings = await validator.scan_file(test_file)

        # Should handle large results efficiently
        assert len(findings) == 1000
        assert findings[0]["rule_id"] == "rule-0"
        assert findings[999]["rule_id"] == "rule-999"
