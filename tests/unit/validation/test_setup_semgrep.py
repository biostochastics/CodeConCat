"""Unit tests for the Semgrep setup module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codeconcat.errors import ValidationError
from codeconcat.validation.setup_semgrep import install_apiiro_ruleset, install_semgrep


class TestSetupSemgrep:
    """Test suite for the Semgrep setup functions."""

    @patch("subprocess.run")
    def test_install_semgrep_success(self, mock_run):
        """Test successful installation of semgrep."""
        # Mock both pip install and semgrep --version calls
        mock_pip_result = MagicMock()
        mock_pip_result.returncode = 0
        mock_pip_result.stdout = "Successfully installed semgrep-1.52.0"
        mock_pip_result.stderr = ""

        mock_version_result = MagicMock()
        mock_version_result.returncode = 0
        mock_version_result.stdout = "1.52.0"
        mock_version_result.stderr = ""

        mock_run.side_effect = [mock_pip_result, mock_version_result]

        result = install_semgrep()
        assert result is True
        # Verify both calls were made
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_install_semgrep_failure(self, mock_run):
        """Test failed installation of semgrep."""
        # Mock installation failure
        mock_run.side_effect = Exception("Installation failed")

        result = install_semgrep()
        assert result is False
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_apiiro_ruleset_success(self, mock_run, tmp_path):
        """Test successful installation of Apiiro ruleset."""
        # Mock all 4 git subprocess calls (clone, fetch, checkout, rev-parse)
        mock_success = MagicMock()
        mock_success.returncode = 0
        mock_success.stdout = ""
        mock_success.stderr = ""

        mock_revparse_result = MagicMock()
        mock_revparse_result.returncode = 0
        # Return the expected commit hash for rev-parse (must match APIIRO_RULESET_COMMIT)
        mock_revparse_result.stdout = "a21246b666f34db899f0e33add7237ed70fab790"
        mock_revparse_result.stderr = ""

        # git clone, git fetch, git checkout, git rev-parse
        mock_run.side_effect = [mock_success, mock_success, mock_success, mock_revparse_result]

        # Create mock rule files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            rule_file = temp_path / "rule.yaml"
            rule_file.touch()

            with patch(
                "tempfile.TemporaryDirectory",
                return_value=MagicMock(__enter__=lambda *_args: temp_dir),
            ), patch("pathlib.Path.glob", return_value=[rule_file]), patch(
                "pathlib.Path.mkdir"
            ), patch("shutil.copy"):
                result = install_apiiro_ruleset(str(tmp_path))
                assert result == str(tmp_path)
                # Verify all 4 git calls were made (clone, fetch, checkout, rev-parse)
                assert mock_run.call_count == 4

    @patch("subprocess.run")
    def test_install_apiiro_ruleset_failure(self, mock_run, tmp_path):
        """Test failed installation of Apiiro ruleset."""
        # Mock git clone failure
        mock_run.side_effect = Exception("Clone failed")

        with pytest.raises(ValidationError) as excinfo:
            install_apiiro_ruleset(str(tmp_path))

        assert "Error installing Apiiro ruleset" in str(excinfo.value)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_apiiro_ruleset_command_failure(self, mock_run, tmp_path):
        """Test failed command execution during Apiiro ruleset installation."""
        # Mock command failure
        mock_run.side_effect = Exception("Command failed")

        with pytest.raises(ValidationError) as excinfo:
            install_apiiro_ruleset(str(tmp_path))

        assert "Error installing Apiiro ruleset" in str(excinfo.value)
        mock_run.assert_called_once()
