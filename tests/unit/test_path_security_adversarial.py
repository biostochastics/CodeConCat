"""
Adversarial test suite for path security module.

This test suite attempts to exploit the path validation logic with various
attack patterns to prove the security hardening is effective.

Test categories:
1. Path traversal attacks (../, ..\, encoded variations)
2. Symlink escape attempts
3. Null byte injection
4. Cross-platform path manipulation (Windows vs Unix)
5. Boundary cases and edge conditions
"""

import os
import tempfile
from pathlib import Path

import pytest

from codeconcat.utils.path_security import PathTraversalError, validate_safe_path


class TestPathTraversalAttacks:
    """Test resistance to path traversal attacks."""

    def test_basic_traversal_attack(self, tmp_path):
        """Attempt basic ../../../etc/passwd style attack."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError, match="escape"):
            validate_safe_path("../../../etc/passwd", base_path=base)

    def test_traversal_then_return(self, tmp_path):
        """Attempt ../sibling/file attack."""
        base = tmp_path / "project"
        base.mkdir()
        sibling = tmp_path / "sibling"
        sibling.mkdir()

        with pytest.raises(PathTraversalError, match="escape"):
            validate_safe_path("../sibling/secret.txt", base_path=base)

    def test_encoded_traversal(self, tmp_path):
        """Attempt URL-encoded path traversal."""
        base = tmp_path / "project"
        base.mkdir()

        # %2e%2e%2f = ../
        with pytest.raises((PathTraversalError, OSError)):
            validate_safe_path("%2e%2e%2f%2e%2e%2fetc%2fpasswd", base_path=base)

    def test_unicode_traversal(self, tmp_path):
        """Attempt Unicode homoglyph attack."""
        base = tmp_path / "project"
        base.mkdir()

        # U+2024 is a dot character that might bypass naive checks
        with pytest.raises((PathTraversalError, OSError)):
            validate_safe_path("\u2024\u2024/\u2024\u2024/etc/passwd", base_path=base)

    def test_double_encoded_traversal(self, tmp_path):
        """Attempt double-encoded traversal."""
        base = tmp_path / "project"
        base.mkdir()

        # %252e%252e%252f = URL-encoded %2e%2e%2f
        with pytest.raises((PathTraversalError, OSError)):
            validate_safe_path("%252e%252e%252fetc%252fpasswd", base_path=base)

    def test_mixed_separators(self, tmp_path):
        """Attempt attack with mixed path separators."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError, match="escape"):
            validate_safe_path("..\\..\\..\\etc\\passwd", base_path=base)

    def test_absolute_path_escape(self, tmp_path):
        """Attempt to access absolute path outside base."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError, match="escape"):
            validate_safe_path("/etc/passwd", base_path=base)


class TestSymlinkAttacks:
    """Test resistance to symlink-based attacks."""

    def test_symlink_to_outside_directory(self, tmp_path):
        """Create symlink pointing outside base directory."""
        base = tmp_path / "project"
        base.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("secret data")

        link = base / "link"
        link.symlink_to(outside)

        # Should block symlinks by default
        with pytest.raises(PathTraversalError, match="Symlink"):
            validate_safe_path("link/secret.txt", base_path=base, allow_symlinks=False)

    def test_symlink_escape_chain(self, tmp_path):
        """Create chain of symlinks that eventually escape."""
        base = tmp_path / "project"
        base.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        link1 = base / "link1"
        link1.symlink_to(base / "link2")
        link2 = base / "link2"
        link2.symlink_to(outside)

        with pytest.raises(PathTraversalError):
            validate_safe_path("link1/file.txt", base_path=base, allow_symlinks=False)

    def test_symlink_to_absolute_path(self, tmp_path):
        """Symlink to absolute path outside base."""
        base = tmp_path / "project"
        base.mkdir()

        link = base / "etc"
        try:
            link.symlink_to("/etc")
        except OSError:
            pytest.skip("Cannot create symlink (permissions)")

        with pytest.raises(PathTraversalError):
            validate_safe_path("etc/passwd", base_path=base, allow_symlinks=False)


class TestNullByteAttacks:
    """Test resistance to null byte injection."""

    def test_null_byte_in_path(self, tmp_path):
        """Attempt null byte injection."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError, match="null byte"):
            validate_safe_path("file.txt\x00../../../etc/passwd", base_path=base)

    def test_null_byte_truncation(self, tmp_path):
        """Attempt truncation attack with null byte."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError, match="null byte"):
            validate_safe_path("safe\x00dangerous", base_path=base)


class TestCrossPlatformAttacks:
    """Test resistance to cross-platform path manipulation."""

    def test_windows_drive_letter_attack(self, tmp_path):
        """Attempt Windows drive letter attack on Unix."""
        base = tmp_path / "project"
        base.mkdir()

        # C:\ should be rejected if not on Windows
        with pytest.raises((PathTraversalError, ValueError)):
            validate_safe_path("C:\\Windows\\System32", base_path=base)

    def test_unc_path_attack(self, tmp_path):
        """Attempt UNC path attack."""
        base = tmp_path / "project"
        base.mkdir()

        # \\server\share should be rejected
        with pytest.raises((PathTraversalError, ValueError)):
            validate_safe_path("\\\\server\\share\\file.txt", base_path=base)

    def test_long_path_attack(self, tmp_path):
        """Attempt attack with extremely long path."""
        base = tmp_path / "project"
        base.mkdir()

        # Create path with 1000+ components
        long_path = "/".join(["a"] * 1000)

        with pytest.raises((PathTraversalError, OSError)):
            validate_safe_path(long_path, base_path=base)


class TestBoundaryEnforcement:
    """Test strict boundary enforcement."""

    def test_valid_path_allowed(self, tmp_path):
        """Verify valid paths within boundary are allowed."""
        base = tmp_path / "project"
        base.mkdir()
        subdir = base / "src"
        subdir.mkdir()
        (subdir / "file.py").write_text("# code")

        # Should succeed
        result = validate_safe_path("src/file.py", base_path=base)
        assert result.exists()
        assert str(result).startswith(str(base))

    def test_boundary_at_base(self, tmp_path):
        """Test that base path itself is valid."""
        base = tmp_path / "project"
        base.mkdir()

        result = validate_safe_path(".", base_path=base)
        assert result == base.resolve()

    def test_empty_path_rejected(self, tmp_path):
        """Empty paths should be rejected."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(ValueError, match="empty"):
            validate_safe_path("", base_path=base)

    def test_path_outside_different_drive(self, tmp_path):
        """Cross-drive access should be rejected."""
        base = tmp_path / "project"
        base.mkdir()

        # On Windows, D:\ vs C:\, on Unix different mount points
        with pytest.raises((PathTraversalError, ValueError)):
            validate_safe_path("/mnt/other/file.txt", base_path=base)


class TestRealWorldScenarios:
    """Test real-world attack scenarios."""

    def test_git_directory_escape(self, tmp_path):
        """Attempt to access .git directory outside project."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError):
            validate_safe_path("../.git/config", base_path=base)

    def test_ssh_key_access_attempt(self, tmp_path):
        """Attempt to access SSH keys."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError):
            validate_safe_path("../../../../home/user/.ssh/id_rsa", base_path=base)

    def test_env_file_access(self, tmp_path):
        """Attempt to access .env files outside project."""
        base = tmp_path / "project"
        base.mkdir()

        with pytest.raises(PathTraversalError):
            validate_safe_path("../../.env", base_path=base)

    def test_npm_package_escape(self, tmp_path):
        """Simulate malicious npm package attempting file access."""
        base = tmp_path / "project" / "node_modules" / "malicious-pkg"
        base.mkdir(parents=True)

        # Malicious package tries to access parent project files
        with pytest.raises(PathTraversalError):
            validate_safe_path("../../../package.json", base_path=base)


class TestDefenseInDepth:
    """Test defense-in-depth mechanisms."""

    def test_canonicalization_happens(self, tmp_path):
        """Verify paths are canonicalized (resolved)."""
        base = tmp_path / "project"
        base.mkdir()
        subdir = base / "src"
        subdir.mkdir()

        # Path with redundant components
        result = validate_safe_path("./src/./subdir/../file.py", base_path=base)

        # Should be canonicalized
        assert "./" not in str(result)
        assert str(result).startswith(str(base))

    def test_commonpath_check(self, tmp_path):
        """Verify commonpath check is performed."""
        base = tmp_path / "project"
        base.mkdir()

        # Even if a path resolves to something, it must share common base
        with pytest.raises(PathTraversalError):
            validate_safe_path("/etc/../etc/passwd", base_path=base)

    def test_string_prefix_check(self, tmp_path):
        """Verify string prefix check is performed (defense-in-depth)."""
        base = tmp_path / "project"
        base.mkdir()

        # Attempt to fool common path check
        with pytest.raises(PathTraversalError):
            validate_safe_path("../../other_project_similar_name", base_path=base)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
