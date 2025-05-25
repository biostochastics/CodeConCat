"""Unit tests for the Semgrep setup module."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from codeconcat.validation.setup_semgrep import install_semgrep, install_apiiro_ruleset
from codeconcat.errors import ValidationError


class TestSetupSemgrep:
    """Test suite for the Semgrep setup functions."""

    @patch('subprocess.run')
    def test_install_semgrep_success(self, mock_run):
        """Test successful installation of semgrep."""
        # Mock successful installation
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = 'Successfully installed semgrep'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        result = install_semgrep()
        assert result is True
        mock_run.assert_called_once_with(
            ["pip", "install", "semgrep"],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_install_semgrep_failure(self, mock_run):
        """Test failed installation of semgrep."""
        # Mock installation failure
        mock_run.side_effect = Exception("Installation failed")
        
        result = install_semgrep()
        assert result is False
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_install_apiiro_ruleset_success(self, mock_run, tmp_path):
        """Test successful installation of Apiiro ruleset."""
        # Mock successful git clone
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = 'Cloning into...'
        mock_process.stderr = ''
        mock_run.return_value = mock_process
        
        # Create mock rule files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            rule_file = temp_path / "rule.yaml"
            rule_file.touch()
            
            with patch('tempfile.TemporaryDirectory', return_value=MagicMock(__enter__=lambda *args: temp_dir)):
                with patch('pathlib.Path.glob', return_value=[rule_file]):
                    with patch('pathlib.Path.mkdir'):
                        with patch('shutil.copy'):
                            result = install_apiiro_ruleset(str(tmp_path))
                            assert result == str(tmp_path)
                            mock_run.assert_called_once()
                            assert "git" in mock_run.call_args[0][0][0]
                            assert "clone" in mock_run.call_args[0][0][1]

    @patch('subprocess.run')
    def test_install_apiiro_ruleset_failure(self, mock_run, tmp_path):
        """Test failed installation of Apiiro ruleset."""
        # Mock git clone failure
        mock_run.side_effect = Exception("Clone failed")
        
        with pytest.raises(ValidationError) as excinfo:
            install_apiiro_ruleset(str(tmp_path))
        
        assert "Error installing Apiiro ruleset" in str(excinfo.value)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_install_apiiro_ruleset_command_failure(self, mock_run, tmp_path):
        """Test failed command execution during Apiiro ruleset installation."""
        # Mock command failure
        mock_run.side_effect = Exception("Command failed")
        
        with pytest.raises(ValidationError) as excinfo:
            install_apiiro_ruleset(str(tmp_path))
        
        assert "Error installing Apiiro ruleset" in str(excinfo.value)
        mock_run.assert_called_once()
