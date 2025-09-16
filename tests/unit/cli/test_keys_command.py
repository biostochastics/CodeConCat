"""Unit tests for the CLI keys command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from codeconcat.cli.commands.keys import app

runner = CliRunner()


class TestKeysCommand:
    """Test the keys CLI commands."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock APIKeyManager."""
        with patch("codeconcat.cli.commands.keys.APIKeyManager") as mock:
            yield mock

    def test_list_keys_empty(self, mock_manager):
        """Test listing keys when none are configured."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = None

        # Run command
        result = runner.invoke(app, ["list"])

        # Check output
        assert result.exit_code == 0
        assert "❌ Not configured" in result.output
        assert "💡 Tip: Run 'codeconcat keys setup'" in result.output

    def test_list_keys_with_configured(self, mock_manager):
        """Test listing keys when some are configured."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Mock some keys configured
        def mock_get_key(provider):
            if provider == "openai":
                return "sk-test1234567890abcdefghijklmnopqrst"
            elif provider == "anthropic":
                return "sk-ant-test1234567890abcdefghijklmn"
            return None

        mock_instance.get_key.side_effect = mock_get_key

        # Run command
        result = runner.invoke(app, ["list"])

        # Check output
        assert result.exit_code == 0
        assert "✅ Configured" in result.output
        assert "sk-test123...qrst" in result.output  # Preview format (10 chars + ... + 4 chars)
        assert "sk-ant-tes...klmn" in result.output

    def test_list_keys_show_values(self, mock_manager):
        """Test listing keys with --show-values flag."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Mock a key
        mock_instance.get_key.side_effect = lambda p: (
            "sk-test1234567890abcdefghijklmnopqrst" if p == "openai" else None
        )

        # Run command
        result = runner.invoke(app, ["list", "--show-values"])

        # Check output
        assert result.exit_code == 0
        assert "sk-test1234567890abcdefghijklmnopqrst" in result.output

    def test_set_key_new(self, mock_manager):
        """Test setting a new API key."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = None  # No existing key
        mock_instance._validate_api_key.return_value = True
        mock_instance.set_key.return_value = True

        # Run command with key as argument
        result = runner.invoke(
            app,
            ["set", "openai", "sk-test1234567890abcdefghijklmnopqrst"],
        )

        # Check output
        assert result.exit_code == 0
        assert "✅ API key for openai stored successfully" in result.output

        # Verify calls
        mock_instance.set_key.assert_called_once_with(
            "openai", "sk-test1234567890abcdefghijklmnopqrst", validate=True
        )

    def test_set_key_replace_existing(self, mock_manager):
        """Test replacing an existing API key."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = "sk-old-key"  # Existing key
        mock_instance._validate_api_key.return_value = True
        mock_instance.set_key.return_value = True

        # Run command with confirmation
        result = runner.invoke(
            app,
            ["set", "openai", "sk-new-key"],
            input="y\n",  # Confirm replacement
        )

        # Check output
        assert result.exit_code == 0
        assert "API key for openai already exists" in result.output
        assert "✅ API key for openai stored successfully" in result.output

    def test_set_key_invalid_provider(self, mock_manager):
        """Test setting key for invalid provider."""
        result = runner.invoke(app, ["set", "invalid_provider", "some-key"])

        # Check output
        assert result.exit_code == 1
        assert "❌ Invalid provider: invalid_provider" in result.output
        assert "Valid providers:" in result.output

    def test_delete_key_exists(self, mock_manager):
        """Test deleting an existing key."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = "sk-test-key"
        mock_instance.delete_key.return_value = True

        # Run command with force flag
        result = runner.invoke(app, ["delete", "openai", "--force"])

        # Check output
        assert result.exit_code == 0
        assert "✅ API key for openai deleted successfully" in result.output

        # Verify deletion was called
        mock_instance.delete_key.assert_called_once_with("openai")

    def test_delete_key_not_exists(self, mock_manager):
        """Test deleting a non-existent key."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = None

        # Run command
        result = runner.invoke(app, ["delete", "openai", "--force"])

        # Check output
        assert result.exit_code == 0
        assert "⚠️  No API key found for openai" in result.output

    def test_reset_keys_with_confirmation(self, mock_manager):
        """Test resetting all keys with confirmation."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Mock some existing keys
        def mock_get_key(provider):
            return "test-key" if provider in ["openai", "anthropic"] else None

        mock_instance.get_key.side_effect = mock_get_key
        mock_instance.delete_key.return_value = True

        # Run command with confirmation
        result = runner.invoke(app, ["reset"], input="y\n")

        # Check output
        assert result.exit_code == 0
        assert "This will delete the following API keys:" in result.output
        assert "openai" in result.output
        assert "anthropic" in result.output
        assert "✅ Deleted 2 API key(s)" in result.output

    def test_reset_keys_force(self, mock_manager):
        """Test resetting all keys with --force flag."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Mock one existing key
        mock_instance.get_key.side_effect = lambda p: "test-key" if p == "openai" else None
        mock_instance.delete_key.return_value = True

        # Run command with force flag
        result = runner.invoke(app, ["reset", "--force"])

        # Check output
        assert result.exit_code == 0
        assert "✅ Deleted 1 API key(s)" in result.output

    @pytest.mark.asyncio
    async def test_test_key_valid(self, mock_manager):
        """Test validating a valid API key."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = "sk-test-key"
        mock_instance.test_api_key = AsyncMock(return_value=True)

        # Run command
        with patch("codeconcat.cli.commands.keys.asyncio.run") as mock_run:
            mock_run.return_value = True
            result = runner.invoke(app, ["test", "openai"])

        # Check output
        assert result.exit_code == 0
        assert "✅ API key for openai is valid and working!" in result.output

    @pytest.mark.asyncio
    async def test_test_key_invalid(self, mock_manager):
        """Test validating an invalid API key."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.get_key.return_value = "sk-invalid-key"
        mock_instance.test_api_key = AsyncMock(return_value=False)

        # Run command
        with patch("codeconcat.cli.commands.keys.asyncio.run") as mock_run:
            mock_run.return_value = False
            result = runner.invoke(app, ["test", "openai"])

        # Check output
        assert result.exit_code == 1
        assert "❌ API key for openai failed validation" in result.output

    def test_export_keys_without_values(self, mock_manager):
        """Test exporting keys without actual values."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Mock some keys
        def mock_get_key(provider):
            if provider in ["openai", "anthropic"]:
                return f"sk-{provider}-key"
            return None

        mock_instance.get_key.side_effect = mock_get_key

        # Run command
        result = runner.invoke(app, ["export"])

        # Check output
        assert result.exit_code == 0
        # The output is the JSON directly
        assert '"version": "1.0"' in result.output
        assert '"openai": "***CONFIGURED***"' in result.output
        assert '"anthropic": "***CONFIGURED***"' in result.output

    def test_export_keys_with_values(self, mock_manager):
        """Test exporting keys with actual values."""
        # Setup mock
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Mock a key
        mock_instance.get_key.side_effect = lambda p: ("sk-test-key" if p == "openai" else None)

        # Run command
        result = runner.invoke(app, ["export", "--include-values"])

        # Check output
        assert result.exit_code == 0
        assert "sk-test-key" in result.output
        assert "WARNING: Exported file contains sensitive API keys!" in result.output

    def test_export_keys_to_file(self, mock_manager):
        """Test exporting keys to a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            # Setup mock
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            mock_instance.get_key.side_effect = lambda p: ("sk-test-key" if p == "openai" else None)

            # Run command
            result = runner.invoke(app, ["export", "--output", output_file])

            # Check output
            assert result.exit_code == 0
            assert f"✅ Exported to {output_file}" in result.output

            # Verify file contents
            with open(output_file) as f:
                data = json.load(f)
                assert data["version"] == "1.0"
                assert "openai" in data["keys"]
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_setup_env_storage(self, mock_manager):
        """Test setup with environment storage (read-only)."""
        result = runner.invoke(app, ["setup", "--storage", "env"])

        # Check output
        assert result.exit_code == 0
        assert "Environment storage is read-only" in result.output
        assert "export OPENAI_API_KEY=" in result.output

    def test_setup_invalid_storage(self, mock_manager):
        """Test setup with invalid storage method."""
        result = runner.invoke(app, ["setup", "--storage", "invalid"])

        # Check output
        assert result.exit_code == 1
        assert "❌ Invalid storage method: invalid" in result.output
