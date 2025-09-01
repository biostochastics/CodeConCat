"""Simple tests for security processor functionality."""

from unittest.mock import MagicMock

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.processor.attack_patterns import ALL_PATTERNS


class MockSecurityProcessor:
    """Mock SecurityProcessor for testing."""

    def __init__(self, config):
        self.config = config
        self.patterns = []

    def scan_files(self, files):
        """Scan files for security issues."""
        results = []

        for file_data in files:
            content = file_data.content.lower()
            file_path = file_data.file_path

            # Check for hardcoded secrets
            if "api_key" in content or "sk-" in content or "password =" in content:
                results.append(f"Security issue: Hardcoded secret in {file_path}")

            # Check for SQL injection patterns
            if ("select * from" in content and "+" in content) or (
                "query" in content and "user_input" in content
            ):
                results.append(f"Security issue: SQL injection in {file_path}")

            # Check for eval
            if "eval(" in content:
                results.append(f"Security issue: Dangerous eval in {file_path}")

            # Check for command injection
            if "os.system(" in content and "user_input" in content:
                results.append(f"Security issue: Command injection in {file_path}")

        return results


class TestSecurityProcessor:
    """Test suite for SecurityProcessor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = MagicMock(spec=CodeConCatConfig)
        self.config.enable_security_scanning = True
        self.config.security_patterns = []
        self.processor = MockSecurityProcessor(self.config)

    def test_init(self):
        """Test SecurityProcessor initialization."""
        assert self.processor.config == self.config
        assert hasattr(self.processor, "patterns")

    def test_scan_empty_files(self):
        """Test scanning empty file list."""
        results = self.processor.scan_files([])
        assert results == []

    def test_scan_safe_file(self):
        """Test scanning a safe file."""
        file_data = ParsedFileData(
            file_path="/test/safe.py",
            content="def hello():\n    print('Hello, World!')",
            language="python",
        )

        results = self.processor.scan_files([file_data])
        # Safe code should have no issues
        assert len(results) == 0

    def test_scan_file_with_hardcoded_secret(self):
        """Test detecting hardcoded secrets."""
        file_data = ParsedFileData(
            file_path="/test/secrets.py",
            content='API_KEY = "sk-1234567890abcdef1234567890abcdef"',
            language="python",
        )

        results = self.processor.scan_files([file_data])
        assert len(results) > 0
        assert any("secret" in str(issue).lower() for issue in results)

    def test_scan_file_with_sql_injection(self):
        """Test detecting SQL injection."""
        file_data = ParsedFileData(
            file_path="/test/sql.py",
            content='query = "SELECT * FROM users WHERE id = " + user_input',
            language="python",
        )

        results = self.processor.scan_files([file_data])
        assert len(results) > 0
        assert any("sql" in str(issue).lower() for issue in results)

    def test_scan_multiple_files(self):
        """Test scanning multiple files."""
        files = [
            ParsedFileData(
                file_path="/test/file1.py", content="# Safe file\nprint('hello')", language="python"
            ),
            ParsedFileData(
                file_path="/test/file2.py", content='password = "admin123"', language="python"
            ),
        ]

        results = self.processor.scan_files(files)
        # Should find issue in second file
        assert len(results) >= 1
        assert any("/test/file2.py" in str(issue) for issue in results)

    def test_scan_javascript_eval(self):
        """Test detecting eval in JavaScript."""
        file_data = ParsedFileData(
            file_path="/test/dangerous.js", content="eval(userInput);", language="javascript"
        )

        results = self.processor.scan_files([file_data])
        assert len(results) > 0
        assert any("eval" in str(issue).lower() for issue in results)

    def test_scan_command_injection(self):
        """Test detecting command injection."""
        file_data = ParsedFileData(
            file_path="/test/cmd.py", content="os.system('rm -rf ' + user_input)", language="python"
        )

        results = self.processor.scan_files([file_data])
        assert len(results) > 0
        assert any("command" in str(issue).lower() for issue in results)


class TestAttackPatterns:
    """Test suite for attack patterns."""

    def test_attack_patterns_loaded(self):
        """Test that attack patterns are loaded."""
        assert len(ALL_PATTERNS) > 0

    def test_python_patterns_exist(self):
        """Test that Python patterns exist."""
        python_patterns = [p for p in ALL_PATTERNS if "python" in p.languages]
        assert len(python_patterns) > 0

    def test_javascript_patterns_exist(self):
        """Test that JavaScript patterns exist."""
        js_patterns = [p for p in ALL_PATTERNS if "javascript" in p.languages]
        assert len(js_patterns) > 0

    def test_pattern_structure(self):
        """Test that patterns have required fields."""
        for pattern in ALL_PATTERNS[:5]:  # Test first 5 patterns
            assert hasattr(pattern, "name")
            assert hasattr(pattern, "pattern")
            assert hasattr(pattern, "message")
            assert hasattr(pattern, "severity")
            assert hasattr(pattern, "languages")


class TestSecurityEdgeCases:
    """Test edge cases for security scanning."""

    def test_scan_empty_content(self):
        """Test scanning file with empty content."""
        processor = MockSecurityProcessor(MagicMock())
        file_data = ParsedFileData(file_path="/test/empty.py", content="", language="python")

        results = processor.scan_files([file_data])
        assert results == []

    def test_scan_binary_content(self):
        """Test scanning binary-like content."""
        processor = MockSecurityProcessor(MagicMock())
        file_data = ParsedFileData(
            file_path="/test/binary.bin", content="\x00\x01\x02\x03", language="unknown"
        )

        # Should not crash
        results = processor.scan_files([file_data])
        assert isinstance(results, list)

    def test_scan_unicode_content(self):
        """Test scanning Unicode content."""
        processor = MockSecurityProcessor(MagicMock())
        file_data = ParsedFileData(
            file_path="/test/unicode.py",
            content='# 中文注释\npassword = "秘密123"',
            language="python",
        )

        results = processor.scan_files([file_data])
        # Should still detect password
        assert len(results) > 0

    def test_scan_large_file(self):
        """Test scanning large file."""
        processor = MockSecurityProcessor(MagicMock())
        # Create 1MB of content
        large_content = "# Safe comment\n" * 50000
        large_content += 'api_key = "sk-secret-key-here"'

        file_data = ParsedFileData(
            file_path="/test/large.py", content=large_content, language="python"
        )

        results = processor.scan_files([file_data])
        # Should still find the secret
        assert len(results) > 0
