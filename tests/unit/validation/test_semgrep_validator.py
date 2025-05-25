"""Unit tests for the Semgrep validator module."""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from codeconcat.validation.semgrep_validator import SemgrepValidator, semgrep_validator
from codeconcat.errors import ValidationError


class TestSemgrepValidator:
    """Test suite for the SemgrepValidator class."""

    def test_init(self):
        """Test initializing the validator."""
        with patch('shutil.which', return_value='/usr/bin/semgrep'):
            validator = SemgrepValidator()
            assert validator.semgrep_path == '/usr/bin/semgrep'
            assert validator.ruleset_path is not None

    def test_init_custom_ruleset(self):
        """Test initializing with a custom ruleset."""
        with patch('shutil.which', return_value='/usr/bin/semgrep'):
            validator = SemgrepValidator(ruleset_path='/custom/ruleset')
            assert validator.semgrep_path == '/usr/bin/semgrep'
            assert validator.ruleset_path == '/custom/ruleset'

    def test_is_available_true(self):
        """Test checking if semgrep is available (when it is)."""
        with patch('shutil.which', return_value='/usr/bin/semgrep'):
            validator = SemgrepValidator()
            assert validator.is_available() is True

    def test_is_available_false(self):
        """Test checking if semgrep is available (when it isn't)."""
        with patch('shutil.which', return_value=None):
            validator = SemgrepValidator()
            assert validator.is_available() is False

    @patch('subprocess.run')
    def test_scan_file(self, mock_run, tmp_path):
        """Test scanning a file for security issues."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text('print("Hello, world!")')
        
        # Mock the subprocess.run output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ''
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Mock the results file content
        mock_results = {
            "results": [
                {
                    "check_id": "test-rule",
                    "path": str(test_file),
                    "start": {"line": 1, "col": 1},
                    "end": {"line": 1, "col": 10},
                    "extra": {
                        "message": "Test finding",
                        "severity": "WARNING",
                        "lines": "print(\"Hello, world!\")"
                    }
                }
            ]
        }
        
        # Use patch to mock open for specific file
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_results))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.open'):
                    with patch('shutil.which', return_value='/usr/bin/semgrep'):
                        validator = SemgrepValidator()
                        findings = validator.scan_file(test_file)
                        
                        assert len(findings) == 1
                        assert findings[0]["type"] == "semgrep"
                        assert findings[0]["rule_id"] == "test-rule"
                        assert findings[0]["message"] == "Test finding"
                        assert findings[0]["severity"] == "WARNING"

    def test_scan_file_semgrep_not_available(self, tmp_path):
        """Test scanning when semgrep isn't available."""
        test_file = tmp_path / "test.py"
        test_file.write_text('print("Hello, world!")')
        
        with patch('shutil.which', return_value=None):
            validator = SemgrepValidator()
            with pytest.raises(ValidationError) as excinfo:
                validator.scan_file(test_file)
            
            assert "Semgrep is not installed" in str(excinfo.value)

    def test_scan_file_nonexistent_file(self):
        """Test scanning a file that doesn't exist."""
        with patch('shutil.which', return_value='/usr/bin/semgrep'):
            validator = SemgrepValidator()
            with pytest.raises(ValidationError) as excinfo:
                validator.scan_file("/nonexistent/file.py")
            
            assert "File does not exist" in str(excinfo.value)

    @patch('subprocess.run')
    def test_scan_directory(self, mock_run, tmp_path):
        """Test scanning a directory for security issues."""
        # Create a test directory with files
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        # Create a test file
        test_file = test_dir / "test.py"
        test_file.write_text('print("Hello, world!")')
        
        # Mock the subprocess.run output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ''
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Mock the results file content
        mock_results = {
            "results": [
                {
                    "check_id": "test-rule",
                    "path": str(test_file),
                    "start": {"line": 1, "col": 1},
                    "end": {"line": 1, "col": 10},
                    "extra": {
                        "message": "Test finding",
                        "severity": "WARNING",
                        "lines": "print(\"Hello, world!\")"
                    }
                }
            ]
        }
        
        # Use patch to mock open for specific file
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_results))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.open'):
                    with patch('shutil.which', return_value='/usr/bin/semgrep'):
                        validator = SemgrepValidator()
                        findings = validator.scan_directory(test_dir)
                        
                        assert str(test_file) in findings
                        assert len(findings[str(test_file)]) == 1
                        assert findings[str(test_file)][0]["type"] == "semgrep"
                        assert findings[str(test_file)][0]["rule_id"] == "test-rule"
                        assert findings[str(test_file)][0]["severity"] == "WARNING"

    def test_detect_language(self, tmp_path):
        """Test language detection for semgrep."""
        with patch('codeconcat.parser.file_parser.determine_language', side_effect=lambda x: {
            "test.py": "python",
            "test.js": "javascript",
            "test.java": "java",
            "test.unknown": "unknown"
        }.get(os.path.basename(x), None)):
            with patch('shutil.which', return_value='/usr/bin/semgrep'):
                validator = SemgrepValidator()
                
                # Python file
                assert validator._detect_language(Path("test.py")) == "python"
                
                # JavaScript file
                assert validator._detect_language(Path("test.js")) == "js"
                
                # Java file
                assert validator._detect_language(Path("test.java")) == "java"
                
                # Unknown file type
                assert validator._detect_language(Path("test.unknown")) is None
