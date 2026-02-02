"""Tests for Apiiro malicious code ruleset integration."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codeconcat.errors import ValidationError
from codeconcat.validation.semgrep_validator import SemgrepValidator
from codeconcat.validation.setup_semgrep import APIIRO_RULESET_COMMIT, install_apiiro_ruleset


class TestApiiroRuleset:
    """Test suite for Apiiro malicious code ruleset."""

    def test_install_apiiro_ruleset_success(self, tmp_path):
        """Test successful installation of Apiiro ruleset."""
        # Mock the git clone command
        with patch("subprocess.run") as mock_run:
            # Create mock yaml files in the temp directory
            mock_run.return_value = MagicMock(returncode=0)

            # Create a fake git clone side effect
            def fake_git_clone(cmd, **_kwargs):
                if "git" in cmd[0] and "clone" in cmd[1]:
                    # Create some fake rule files in the temp directory
                    # Command is: ["git", "clone", "--depth", "1", URL, temp_dir]
                    temp_dir = Path(cmd[-1])  # Last argument is the target directory

                    # Create directory structure
                    (temp_dir / "rules" / "python").mkdir(parents=True)
                    (temp_dir / "rules" / "javascript").mkdir(parents=True)

                    # Create fake rule files
                    python_rule = temp_dir / "rules" / "python" / "backdoor.yaml"
                    python_rule.write_text(
                        """
rules:
  - id: python-backdoor-detection
    pattern: |
      eval(...)
    message: Potential backdoor using eval
    languages: [python]
    severity: ERROR
"""
                    )

                    js_rule = temp_dir / "rules" / "javascript" / "malicious-code.yaml"
                    js_rule.write_text(
                        """
rules:
  - id: js-malicious-execution
    pattern: |
      exec(...)
    message: Potential malicious code execution
    languages: [javascript]
    severity: ERROR
"""
                    )

                    return MagicMock(returncode=0)
                elif "git" in cmd[0] and "rev-parse" in cmd:
                    # Mock git rev-parse HEAD to return the expected commit hash
                    mock_result = MagicMock(returncode=0)
                    # Configure stdout.strip() to return the imported constant
                    mock_result.stdout.strip.return_value = APIIRO_RULESET_COMMIT
                    return mock_result

                return MagicMock(returncode=0)

            mock_run.side_effect = fake_git_clone

            # Install to test directory
            target_dir = tmp_path / "apiiro-rules"
            result = install_apiiro_ruleset(str(target_dir))

            # Verify installation
            assert result == str(target_dir)
            assert target_dir.exists()

            # Check that files were copied
            assert (target_dir / "rules" / "python" / "backdoor.yaml").exists()
            assert (target_dir / "rules" / "javascript" / "malicious-code.yaml").exists()

    def test_install_apiiro_ruleset_clone_failure(self, tmp_path):
        """Test handling of git clone failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "clone"], stderr="Failed to clone"
            )

            with pytest.raises(ValidationError) as excinfo:
                install_apiiro_ruleset(str(tmp_path / "rules"))

            assert "Failed to install Apiiro ruleset" in str(excinfo.value)

    def test_semgrep_with_apiiro_rules(self, tmp_path):
        """Test running semgrep with Apiiro rules."""
        # Create test files with malicious patterns
        test_dir = tmp_path / "test_code"
        test_dir.mkdir()

        # Python file with eval (backdoor pattern)
        python_file = test_dir / "backdoor.py"
        python_file.write_text(
            """
import os

def run_code(code):
    # This is a backdoor - dangerous!
    eval(code)

def safe_function():
    return "This is safe"
"""
        )

        # JavaScript file with exec
        js_file = test_dir / "malicious.js"
        js_file.write_text(
            """
function executeCode(code) {
    // Dangerous code execution
    exec(code);
}

function normalFunction() {
    console.log("Normal code");
}
"""
        )

        # Create a mock semgrep validator
        validator = SemgrepValidator()

        # Mock the semgrep execution
        with patch("subprocess.run") as mock_run:
            # Create mock semgrep results
            mock_results = {
                "results": [
                    {
                        "path": str(python_file),
                        "check_id": "python-backdoor-detection",
                        "extra": {
                            "message": "Potential backdoor using eval",
                            "severity": "ERROR",
                            "lines": "    eval(code)",
                        },
                        "start": {"line": 6, "col": 5},
                    },
                    {
                        "path": str(js_file),
                        "check_id": "js-malicious-execution",
                        "extra": {
                            "message": "Potential malicious code execution",
                            "severity": "ERROR",
                            "lines": "    exec(code);",
                        },
                        "start": {"line": 4, "col": 5},
                    },
                ]
            }

            # Set up the mock to write results file
            def mock_semgrep_run(cmd, **_kwargs):
                # Find the output file in the command
                output_idx = cmd.index("--output") + 1
                output_file = cmd[output_idx]

                # Write mock results
                with open(output_file, "w") as f:
                    json.dump(mock_results, f)

                return MagicMock(returncode=1, stderr="")  # 1 = findings found

            mock_run.side_effect = mock_semgrep_run

            # Mock is_available
            with patch.object(validator, "is_available", return_value=True):
                # Run scan
                findings = validator.scan_directory(test_dir)

            # Verify findings
            assert str(python_file) in findings
            assert str(js_file) in findings

            # Check Python findings
            python_findings = findings[str(python_file)]
            assert len(python_findings) == 1
            assert python_findings[0]["rule_id"] == "python-backdoor-detection"
            assert python_findings[0]["severity"] == "ERROR"
            assert "eval" in python_findings[0]["message"]

            # Check JavaScript findings
            js_findings = findings[str(js_file)]
            assert len(js_findings) == 1
            assert js_findings[0]["rule_id"] == "js-malicious-execution"
            assert js_findings[0]["severity"] == "ERROR"
            assert "exec" in js_findings[0]["message"]

    def test_apiiro_rules_detect_various_patterns(self, tmp_path):
        """Test that Apiiro rules can detect various malicious patterns."""
        # Create test files with different malicious patterns
        test_dir = tmp_path / "malicious_patterns"
        test_dir.mkdir()

        # Command injection pattern
        cmd_injection = test_dir / "cmd_injection.py"
        cmd_injection.write_text(
            """
import os
import subprocess

def run_user_command(user_input):
    # Command injection vulnerability
    os.system(f"echo {user_input}")
    subprocess.call(user_input, shell=True)
"""
        )

        # SQL injection pattern
        sql_injection = test_dir / "sql_injection.py"
        sql_injection.write_text(
            """
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
"""
        )

        # Hardcoded secrets
        secrets_file = test_dir / "secrets.py"
        secrets_file.write_text(
            """
# Configuration with hardcoded secrets
API_KEY = "sk_live_abcdef123456789"
PASSWORD = "super_secret_password_123"
SECRET_TOKEN = "ghp_1234567890abcdef"
"""
        )

        # Create validator
        validator = SemgrepValidator()

        # Mock semgrep to return various findings
        with patch("subprocess.run") as mock_run:
            mock_results = {
                "results": [
                    {
                        "path": str(cmd_injection),
                        "check_id": "python-command-injection",
                        "extra": {
                            "message": "Potential command injection vulnerability",
                            "severity": "HIGH",
                            "lines": '    os.system(f"echo {user_input}")',
                        },
                        "start": {"line": 7, "col": 5},
                    },
                    {
                        "path": str(sql_injection),
                        "check_id": "python-sql-injection",
                        "extra": {
                            "message": "SQL injection vulnerability",
                            "severity": "HIGH",
                            "lines": '    query = f"SELECT * FROM users WHERE id = {user_id}"',
                        },
                        "start": {"line": 8, "col": 5},
                    },
                    {
                        "path": str(secrets_file),
                        "check_id": "hardcoded-secrets",
                        "extra": {
                            "message": "Hardcoded secret detected",
                            "severity": "MEDIUM",
                            "lines": 'API_KEY = "sk_live_abcdef123456789"',
                        },
                        "start": {"line": 3, "col": 1},
                    },
                ]
            }

            def mock_semgrep_run(cmd, **_kwargs):
                output_idx = cmd.index("--output") + 1
                output_file = cmd[output_idx]
                with open(output_file, "w") as f:
                    json.dump(mock_results, f)
                return MagicMock(returncode=1, stderr="")

            mock_run.side_effect = mock_semgrep_run

            with patch.object(validator, "is_available", return_value=True):
                findings = validator.scan_directory(test_dir)

            # Verify all patterns were detected
            assert len(findings) == 3

            # Verify command injection detection
            assert str(cmd_injection) in findings
            cmd_findings = findings[str(cmd_injection)]
            assert any("command-injection" in f["rule_id"] for f in cmd_findings)

            # Verify SQL injection detection
            assert str(sql_injection) in findings
            sql_findings = findings[str(sql_injection)]
            assert any("sql-injection" in f["rule_id"] for f in sql_findings)

            # Verify hardcoded secrets detection
            assert str(secrets_file) in findings
            secret_findings = findings[str(secrets_file)]
            assert any("hardcoded-secrets" in f["rule_id"] for f in secret_findings)

    def test_apiiro_rules_language_filtering(self, tmp_path):
        """Test that language filtering works with Apiiro rules."""
        validator = SemgrepValidator()

        # Create test directory with mixed languages
        test_dir = tmp_path / "mixed_languages"
        test_dir.mkdir()

        # Python file
        (test_dir / "test.py").write_text("eval('dangerous')")

        # JavaScript file
        (test_dir / "test.js").write_text("exec('dangerous')")

        # Ruby file (should be ignored if we filter for Python only)
        (test_dir / "test.rb").write_text("eval('dangerous')")

        with patch("subprocess.run") as mock_run:
            # Check that language filter is passed to semgrep
            def check_language_filter(cmd, **_kwargs):
                # Verify --lang python is in the command
                assert "--lang" in cmd
                lang_idx = cmd.index("--lang")
                assert cmd[lang_idx + 1] == "python"

                # Return empty results
                output_idx = cmd.index("--output") + 1
                output_file = cmd[output_idx]
                with open(output_file, "w") as f:
                    json.dump({"results": []}, f)

                return MagicMock(returncode=0)

            mock_run.side_effect = check_language_filter

            with patch.object(validator, "is_available", return_value=True):
                # Scan with language filter
                validator.scan_directory(test_dir, languages=["python"])

                # Verify semgrep was called with language filter
                assert mock_run.called
