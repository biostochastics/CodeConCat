"""
Tests for security hardening fixes.

This module tests the security improvements made to address findings from
multi-agent security review (Crush, Gemini, Codex).

Test coverage:
1. exec_patterns regex word boundaries (prevents false positives)
2. Binary detection with Latin-1 fallback (prevents incorrect binary classification)
3. Symlink skip in verify_integrity_manifest (prevents path escape)
4. Path traversal protection in validate_input_files (prevents directory escape)
5. Semgrep version exact matching (prevents version spoofing)
"""

from unittest.mock import MagicMock, patch

import pytest

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.validation.integration import validate_input_files
from codeconcat.validation.security import (
    DANGEROUS_PATTERNS,
    FILE_HASH_CACHE,
    security_validator,
)


class TestExecPatternsWordBoundaries:
    """Test that exec_patterns regex uses word boundaries correctly."""

    def test_system_function_call_detected(self):
        """Ensure os.system() calls are detected."""
        content = "os.system('rm -rf /')"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is not None

    def test_system_variable_name_not_detected(self):
        """Ensure 'system' as part of variable name is NOT detected (word boundary)."""
        content = "system_config = {'host': 'localhost'}"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is None

    def test_evaluation_variable_not_detected(self):
        """Ensure 'eval' as part of variable name is NOT detected."""
        content = "evaluation_score = 0.95"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is None

    def test_execute_variable_not_detected(self):
        """Ensure 'exec' as part of variable name is NOT detected."""
        content = "execute_flag = True"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is None

    def test_exec_function_call_detected(self):
        """Ensure exec() calls are detected."""
        content = "exec(user_input)"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is not None

    def test_eval_function_call_detected(self):
        """Ensure eval() calls are detected."""
        content = "result = eval(expression)"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is not None

    def test_subprocess_popen_detected(self):
        """Ensure subprocess.Popen is detected."""
        content = "proc = subprocess.Popen(['ls', '-la'])"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is not None

    def test_popen_in_variable_name_not_detected(self):
        """Ensure 'popen' in variable name is NOT detected."""
        content = "popen_wrapper_class = MyWrapper"
        assert DANGEROUS_PATTERNS["exec_patterns"].search(content) is None

    def test_file_with_system_variable(self, tmp_path):
        """Test scanning file with 'system' as variable name doesn't flag."""
        test_file = tmp_path / "config.py"
        test_file.write_text(
            """
            system_name = "production"
            system_config = {"timeout": 30}
            evaluation_metrics = []
            """
        )

        findings = security_validator.check_for_suspicious_content(test_file)

        # Should not find exec_patterns
        exec_findings = [f for f in findings if f.get("name") == "exec_patterns"]
        assert len(exec_findings) == 0, "Should not flag variable names"


class TestBinaryDetectionLatin1:
    """Test binary detection with Latin-1 fallback."""

    def test_utf8_text_file_detected_as_text(self, tmp_path):
        """UTF-8 encoded text should be detected as text."""
        test_file = tmp_path / "utf8.txt"
        test_file.write_text("Hello, World!")

        assert security_validator.is_binary_file(test_file) is False

    def test_latin1_text_file_detected_as_text(self, tmp_path):
        """Latin-1 encoded text should be detected as text, not binary."""
        test_file = tmp_path / "latin1.txt"
        # Write Latin-1 encoded content (bytes that are invalid UTF-8 but valid Latin-1)
        # Characters like e-acute (0xe9), n-tilde (0xf1), u-umlaut (0xfc) are valid Latin-1
        latin1_content = b"Caf\xe9 au lait avec cr\xe8me fra\xeeche"
        test_file.write_bytes(latin1_content)

        assert security_validator.is_binary_file(test_file) is False

    def test_windows_1252_text_file_detected_as_text(self, tmp_path):
        """Windows-1252 encoded text should be detected as text."""
        test_file = tmp_path / "win1252.txt"
        # Smart quotes and other Windows-1252 specific characters
        win1252_content = b"He said \x93Hello\x94 and \x96 smiled"
        test_file.write_bytes(win1252_content)

        assert security_validator.is_binary_file(test_file) is False

    def test_binary_with_null_bytes_detected_as_binary(self, tmp_path):
        """Files with null bytes should be detected as binary."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"Binary\x00content\x00with\x00nulls")

        assert security_validator.is_binary_file(test_file) is True

    def test_binary_with_high_control_char_density(self, tmp_path):
        """Files with high control character density should be binary.

        The control char check only counts ASCII control chars (ord < 32, excluding
        tab/newline/carriage return). We need to create content that:
        1. Has no null bytes (so null byte check doesn't trigger first)
        2. Fails UTF-8 decode (so we fall back to Latin-1)
        3. Has >10% ASCII control characters (ord 0x01-0x08, 0x0B, 0x0C, 0x0E-0x1F)
        """
        test_file = tmp_path / "control.bin"
        # Mix of:
        # - Invalid UTF-8 byte (0xFF triggers Latin-1 fallback)
        # - ASCII control chars (0x01-0x08) which are counted
        # - Regular ASCII text
        # Control bytes: 0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08 = 8 bytes
        # 0xFF forces UTF-8 failure
        # "abc" = 3 printable bytes
        # Total: 12 bytes, 8 control = 66% > 10%
        control_content = b"\xff\x01\x02\x03\x04\x05\x06\x07\x08abc"
        test_file.write_bytes(control_content)

        assert security_validator.is_binary_file(test_file) is True

    def test_executable_detected_as_binary(self, tmp_path):
        """ELF/PE executables should be detected as binary."""
        test_file = tmp_path / "program"
        # ELF header
        test_file.write_bytes(b"\x7fELF" + b"\x00" * 100)

        assert security_validator.is_binary_file(test_file) is True


class TestSymlinkEscapeInManifestVerification:
    """Test that symlinks are properly skipped in verify_integrity_manifest."""

    def test_symlink_inside_base_is_skipped(self, tmp_path):
        """Symlinks inside base directory should be skipped during verification."""
        base = tmp_path / "project"
        base.mkdir()

        # Create a regular file
        file1 = base / "real_file.txt"
        file1.write_text("real content")

        # Create a symlink to a file outside base
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("secret data")

        link = base / "link_to_outside"
        try:
            link.symlink_to(secret)
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        # Generate manifest (should skip symlinks)
        FILE_HASH_CACHE.clear()
        manifest = security_validator.generate_integrity_manifest(base)

        # Verify manifest only contains the real file
        assert "real_file.txt" in manifest
        assert "link_to_outside" not in manifest

    def test_symlink_escape_blocked_in_verify(self, tmp_path):
        """Symlinks pointing outside should not be processed during verification."""
        base = tmp_path / "project"
        base.mkdir()

        # Create files
        file1 = base / "file1.txt"
        file1.write_text("content 1")

        # Create a symlink to /etc (or another outside location)
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "external.txt").write_text("external data")

        link = base / "external_link"
        try:
            link.symlink_to(outside / "external.txt")
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        # Generate manifest first
        FILE_HASH_CACHE.clear()
        manifest = security_validator.generate_integrity_manifest(base)

        # Add a new file after manifest generation (simulating supply chain attack)
        new_file = base / "new_file.txt"
        new_file.write_text("new content")

        # Verify manifest - should detect new_file but not process symlink
        FILE_HASH_CACHE.clear()
        results = security_validator.verify_integrity_manifest(base, manifest)

        # The new_file should be flagged as unexpected
        assert "new_file.txt" in results
        assert results["new_file.txt"]["unexpected"] is True

        # The symlink should not cause issues (no escape)
        # It should either be skipped entirely or marked as unverified
        symlink_results = {p: r for p, r in results.items() if "external_link" in p}
        for path, result in symlink_results.items():
            # Any symlink that appears in results must NOT be marked as verified
            assert result.get("verified") is False, (
                f"Symlink '{path}' should not be verified (was: {result})"
            )


class TestPathTraversalInValidateInputFiles:
    """Test path traversal protection in validate_input_files."""

    def test_valid_file_within_base_passes(self, tmp_path):
        """Files within the base directory should pass validation."""
        # Create test file
        file1 = tmp_path / "src" / "main.py"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("def main(): pass")

        files_to_process = [
            ParsedFileData(
                file_path=str(file1),
                content="def main(): pass",
                language="python",
            )
        ]

        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = str(tmp_path)
        config.strict_validation = False
        config.enable_security_scanning = False
        config.max_file_size = 10 * 1024 * 1024

        validated = validate_input_files(files_to_process, config)
        assert len(validated) == 1

    def test_path_traversal_attack_blocked(self, tmp_path):
        """Path traversal attempts should be blocked."""
        # Create a file outside the target directory
        outside = tmp_path / "outside"
        outside.mkdir()
        secret_file = outside / "secret.txt"
        secret_file.write_text("secret data")

        # Create target directory
        project = tmp_path / "project"
        project.mkdir()

        # Attempt traversal
        traversal_path = str(project / ".." / "outside" / "secret.txt")

        files_to_process = [
            ParsedFileData(
                file_path=traversal_path,
                content="secret data",
                language="text",
            )
        ]

        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = str(project)
        config.strict_validation = False
        config.enable_security_scanning = False
        config.max_file_size = 10 * 1024 * 1024

        # Should filter out the traversal attempt (logged as validation error)
        validated = validate_input_files(files_to_process, config)
        assert len(validated) == 0

    def test_symlink_to_outside_blocked(self, tmp_path):
        """Symlinks pointing outside should be blocked."""
        # Create outside file
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("secret")

        # Create project with symlink
        project = tmp_path / "project"
        project.mkdir()

        link = project / "link"
        try:
            link.symlink_to(secret)
        except OSError:
            pytest.skip("Cannot create symlinks")

        files_to_process = [
            ParsedFileData(
                file_path=str(link),
                content="secret",
                language="text",
            )
        ]

        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = str(project)
        config.strict_validation = False
        config.enable_security_scanning = False
        config.max_file_size = 10 * 1024 * 1024

        # Should block symlink
        validated = validate_input_files(files_to_process, config)
        assert len(validated) == 0


class TestSemgrepVersionVerification:
    """Test Semgrep version verification improvements."""

    @patch("codeconcat.validation.setup_semgrep.subprocess.run")
    @patch("codeconcat.validation.setup_semgrep.shutil.which")
    def test_exact_version_match_passes(self, mock_which, mock_run):
        """Exact version match should pass."""
        from codeconcat.validation.setup_semgrep import SEMGREP_VERSION, install_semgrep

        mock_which.return_value = "/usr/bin/semgrep"

        # First call is pip install (success), second is version check
        install_result = MagicMock()
        install_result.returncode = 0
        install_result.stdout = "Successfully installed semgrep"

        version_result = MagicMock()
        version_result.stdout = SEMGREP_VERSION  # Exact match

        mock_run.side_effect = [install_result, version_result]

        # Should succeed without warnings
        result = install_semgrep()
        assert result is True

    @patch("codeconcat.validation.setup_semgrep.subprocess.run")
    @patch("codeconcat.validation.setup_semgrep.shutil.which")
    @patch("codeconcat.validation.setup_semgrep.logger")
    def test_version_with_suffix_triggers_warning(self, mock_logger, mock_which, mock_run):
        """Version with suffix (potential spoofing) should trigger warning."""
        from codeconcat.validation.setup_semgrep import SEMGREP_VERSION, install_semgrep

        mock_which.return_value = "/usr/bin/semgrep"

        install_result = MagicMock()
        install_result.returncode = 0
        install_result.stdout = "Successfully installed semgrep"

        version_result = MagicMock()
        # Spoofed version that would pass substring check
        version_result.stdout = f"{SEMGREP_VERSION}-exploit"

        mock_run.side_effect = [install_result, version_result]

        result = install_semgrep()

        # Should return False on version mismatch (security: don't trust unexpected versions)
        assert result is False
        # Check that warning was logged about version mismatch
        mock_logger.warning.assert_called()


class TestApiiroCommitVerification:
    """Test Apiiro ruleset commit verification."""

    def test_commit_hash_format_valid(self):
        """Verify the commit hash is a valid 40-character hex string."""
        from codeconcat.validation.setup_semgrep import APIIRO_RULESET_COMMIT

        assert len(APIIRO_RULESET_COMMIT) == 40
        assert all(c in "0123456789abcdef" for c in APIIRO_RULESET_COMMIT.lower())

    def test_commit_hash_not_placeholder(self):
        """Verify the commit hash is not the old placeholder."""
        from codeconcat.validation.setup_semgrep import APIIRO_RULESET_COMMIT

        # The old invalid placeholder
        old_placeholder = "c8e8fc2d90e5a3b6d7f1e9c4a2b5d8f3e6c9a1b4"
        assert (
            old_placeholder != APIIRO_RULESET_COMMIT
        ), "Commit hash should be updated from placeholder"


class TestSecretsPatternAccuracy:
    """Test that secrets pattern has correct keyword restrictions."""

    def test_server_name_not_flagged(self):
        """server_name should NOT be flagged (not a secret keyword)."""
        content = 'server_name = "production-web-01"'
        assert DANGEROUS_PATTERNS["secrets_pattern"].search(content) is None

    def test_version_string_not_flagged(self):
        """Version strings should NOT be flagged."""
        content = 'version = "1.2.3.4.5.6.7.8"'
        assert DANGEROUS_PATTERNS["secrets_pattern"].search(content) is None

    def test_password_flagged(self):
        """password assignments should be flagged."""
        content = 'password = "super_secret123"'
        assert DANGEROUS_PATTERNS["secrets_pattern"].search(content) is not None

    def test_api_key_flagged(self):
        """API key assignments should be flagged."""
        content = 'api_key = "sk-abcdefghijklmnop"'
        assert DANGEROUS_PATTERNS["secrets_pattern"].search(content) is not None

    def test_secret_flagged(self):
        """secret assignments should be flagged."""
        content = 'secret = "my_secret_value123"'
        assert DANGEROUS_PATTERNS["secrets_pattern"].search(content) is not None

    def test_short_values_not_flagged(self):
        """Values shorter than 8 characters should NOT be flagged."""
        content = 'password = "short"'
        assert DANGEROUS_PATTERNS["secrets_pattern"].search(content) is None
