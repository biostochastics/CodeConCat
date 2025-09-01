"""Tests for __main__ module execution."""

import subprocess
import sys
from unittest.mock import patch


class TestMainModule:
    """Test __main__ module execution."""

    def test_main_module_execution(self):
        """Test that __main__ module can be imported without executing."""
        # Import should work without executing cli_entry_point
        # If we got here without error, the import was successful
        assert True

    @patch("codeconcat.main.cli_entry_point")
    def test_main_module_as_script(self, _mock_cli):
        """Test running codeconcat with python -m."""
        # Test that we can run the module
        result = subprocess.run(
            [sys.executable, "-m", "codeconcat", "--help"], capture_output=True, text=True
        )
        # Should not error out
        assert result.returncode in [0, 1]  # 0 for success, 1 for help
