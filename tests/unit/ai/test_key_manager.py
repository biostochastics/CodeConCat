"""Comprehensive tests for API key management."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codeconcat.ai.key_manager import APIKeyManager, KeyStorage, setup_api_keys


class TestAPIKeyManager:
    """Test API key management functionality."""

    @pytest.fixture
    def temp_home(self, tmp_path):
        """Create a temporary home directory for testing."""
        return tmp_path

    @pytest.fixture
    def key_manager(self, temp_home, monkeypatch):
        """Create a key manager with temporary storage."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)
        return APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)

    def test_init_creates_config_dir(self, temp_home, monkeypatch):
        """Test that initialization creates the config directory."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)
        _ = APIKeyManager()  # This creates the config directory

        config_dir = temp_home / ".codeconcat"
        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_validate_api_key_openai(self, key_manager):
        """Test OpenAI API key validation."""
        # Valid formats
        assert key_manager._validate_api_key("openai", "sk-proj-abcd1234567890")
        assert key_manager._validate_api_key("openai", "sk-1234567890abcdef")
        assert key_manager._validate_api_key("openai", "sess-abcd1234567890")

        # Invalid formats
        assert not key_manager._validate_api_key("openai", "invalid-key")
        assert not key_manager._validate_api_key("openai", "")
        assert not key_manager._validate_api_key("openai", "short")
        assert not key_manager._validate_api_key("openai", "xk-1234567890")

    def test_validate_api_key_anthropic(self, key_manager):
        """Test Anthropic API key validation."""
        # Valid format
        assert key_manager._validate_api_key("anthropic", "sk-ant-api03-abcd1234567890")

        # Invalid formats
        assert not key_manager._validate_api_key("anthropic", "sk-abcd1234567890")
        assert not key_manager._validate_api_key("anthropic", "invalid-key")
        assert not key_manager._validate_api_key("anthropic", "")

    def test_validate_api_key_openrouter(self, key_manager):
        """Test OpenRouter API key validation."""
        # Valid format
        assert key_manager._validate_api_key("openrouter", "sk-or-v1-abcd1234567890")

        # Invalid formats
        assert not key_manager._validate_api_key("openrouter", "sk-abcd1234567890")
        assert not key_manager._validate_api_key("openrouter", "invalid-key")

    def test_validate_api_key_unknown_provider(self, key_manager):
        """Test validation for unknown providers."""
        # Should accept any key >= 20 chars
        assert key_manager._validate_api_key("unknown", "a" * 20)
        assert key_manager._validate_api_key("custom", "custom-key-1234567890abcdef")

        # Should reject short keys
        assert not key_manager._validate_api_key("unknown", "short")
        assert not key_manager._validate_api_key("custom", "")

    def test_get_key_from_environment(self, key_manager, monkeypatch):
        """Test retrieving API keys from environment variables."""
        # Set environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")

        # Test retrieval
        assert key_manager.get_key("openai") == "sk-test-openai-key"
        assert key_manager.get_key("anthropic") == "sk-ant-test-key"
        assert key_manager.get_key("openrouter") == "sk-or-test-key"

        # Test caching
        assert "openai" in key_manager._keys_cache
        assert key_manager._keys_cache["openai"] == "sk-test-openai-key"

    def test_get_key_not_found(self, key_manager, monkeypatch):
        """Test behavior when key is not found."""
        # Clear any environment variables
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        assert key_manager.get_key("nonexistent") is None
        assert key_manager.get_key("openai") is None

    @patch("getpass.getpass")
    def test_set_and_get_encrypted_key(self, mock_getpass, key_manager, monkeypatch):
        """Test storing and retrieving encrypted keys."""
        # Clear environment variables
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        mock_getpass.return_value = "test-password"

        # Store a key
        success = key_manager.set_key("openai", "sk-test-key-1234567890abcdef", validate=False)
        assert success

        # Clear cache to force retrieval from file
        key_manager._keys_cache.clear()
        key_manager._fernet = None

        # Retrieve the key
        retrieved_key = key_manager.get_key("openai")
        assert retrieved_key == "sk-test-key-1234567890abcdef"

    @patch("getpass.getpass")
    def test_delete_encrypted_key(self, mock_getpass, key_manager, monkeypatch):
        """Test deleting encrypted keys."""
        # Clear environment variables
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        mock_getpass.return_value = "test-password"

        # Store a key
        key_manager.set_key("openai", "sk-test-key-1234567890abcdef", validate=False)

        # Delete the key
        success = key_manager.delete_key("openai")
        assert success

        # Verify it's deleted
        key_manager._keys_cache.clear()
        key_manager._fernet = None
        assert key_manager.get_key("openai") is None

    def test_list_stored_providers(self, key_manager, monkeypatch):
        """Test listing providers with stored keys."""
        # Set environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        providers = key_manager.list_stored_providers()
        assert "openai (env)" in providers
        assert "anthropic (env)" in providers

    @pytest.mark.asyncio
    async def test_test_api_key(self, key_manager):
        """Test API key validation through provider."""
        with patch("codeconcat.ai.factory.get_ai_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.validate_connection = AsyncMock(return_value=True)
            mock_provider.close = AsyncMock()
            mock_get_provider.return_value = mock_provider

            # Test valid key
            result = await key_manager.test_api_key("openai", "sk-test-key")
            assert result is True
            mock_provider.validate_connection.assert_called_once()
            mock_provider.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_api_key_failure(self, key_manager):
        """Test API key validation failure."""
        with patch("codeconcat.ai.factory.get_ai_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.validate_connection = AsyncMock(return_value=False)
            mock_provider.close = AsyncMock()
            mock_get_provider.return_value = mock_provider

            result = await key_manager.test_api_key("openai", "invalid-key")
            assert result is False

    @pytest.mark.asyncio
    async def test_test_api_key_exception(self, key_manager):
        """Test API key validation with exception."""
        with patch("codeconcat.ai.factory.get_ai_provider") as mock_get_provider:
            mock_get_provider.side_effect = Exception("Provider error")

            result = await key_manager.test_api_key("openai", "sk-test-key")
            assert result is False

    def test_keyring_storage_import_error(self, temp_home, monkeypatch):
        """Test keyring storage when keyring is not installed."""
        # Clear environment variables
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        monkeypatch.setattr(Path, "home", lambda: temp_home)
        manager = APIKeyManager(storage_method=KeyStorage.KEYRING)

        # Mock import error
        with patch("builtins.__import__", side_effect=ImportError("No module named 'keyring'")):
            # Should handle gracefully
            key = manager.get_key("openai")
            assert key is None

            # Set should also handle gracefully (returns False due to import error)
            success = manager.set_key("openai", "sk-test-key", validate=False)
            assert not success  # Returns False because keyring is not available

    @patch("keyring.get_password")
    @patch("keyring.set_password")
    def test_keyring_storage_success(self, mock_set, mock_get, temp_home, monkeypatch):
        """Test successful keyring storage operations."""
        # Clear environment variables
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        monkeypatch.setattr(Path, "home", lambda: temp_home)
        manager = APIKeyManager(storage_method=KeyStorage.KEYRING)

        # Test get
        mock_get.return_value = "sk-stored-key"
        key = manager.get_key("openai")
        assert key == "sk-stored-key"
        mock_get.assert_called_with("codeconcat", "api_key_openai")

        # Test set
        mock_set.return_value = None
        success = manager.set_key("anthropic", "sk-ant-new-key", validate=False)
        assert success
        mock_set.assert_called_with("codeconcat", "api_key_anthropic", "sk-ant-new-key")


class TestSetupAPIKeys:
    """Test the interactive API key setup function."""

    @pytest.mark.asyncio
    @patch("codeconcat.ai.key_manager.APIKeyManager")
    @patch("builtins.input")
    @patch("getpass.getpass")
    async def test_setup_api_keys_interactive(self, mock_getpass, mock_input, mock_manager_class):
        """Test interactive API key setup."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Simulate user interaction
        mock_input.side_effect = ["y", "n", "y", "n"]  # Configure OpenAI and OpenRouter
        mock_getpass.side_effect = ["sk-test-openai-key", "sk-or-test-router-key"]

        # Mock validation and testing
        mock_manager._validate_api_key.return_value = True
        mock_manager.test_api_key = AsyncMock(return_value=True)
        mock_manager.set_key.return_value = True
        mock_manager.get_key.return_value = None  # No existing keys

        # Run setup
        result = await setup_api_keys(interactive=True)

        # Verify results
        assert "openai" in result
        assert "openrouter" in result
        assert result["openai"] == "sk-test-openai-key"
        assert result["openrouter"] == "sk-or-test-router-key"

    @pytest.mark.asyncio
    @patch("codeconcat.ai.key_manager.APIKeyManager")
    async def test_setup_api_keys_non_interactive(self, mock_manager_class):
        """Test non-interactive API key setup."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Simulate existing keys
        mock_manager.get_key.side_effect = ["sk-existing-openai", None, None, None]

        # Run setup
        result = await setup_api_keys(interactive=False)

        # Should only return existing keys
        assert "openai" in result
        assert result["openai"] == "sk-existing-openai"
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch("codeconcat.ai.key_manager.APIKeyManager")
    @patch("builtins.input")
    @patch("getpass.getpass")
    async def test_setup_api_keys_validation_failure(
        self, mock_getpass, mock_input, mock_manager_class
    ):
        """Test API key setup with validation failure."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # User wants to configure OpenAI
        mock_input.side_effect = ["y", "n", "n", "n"]
        mock_getpass.return_value = "invalid-key"

        # Mock validation failure
        mock_manager._validate_api_key.return_value = False
        mock_manager.get_key.return_value = None

        # Run setup
        result = await setup_api_keys(interactive=True)

        # Should not store invalid key
        assert "openai" not in result
        assert len(result) == 0

    @pytest.mark.asyncio
    @patch("codeconcat.ai.key_manager.APIKeyManager")
    @patch("builtins.input")
    @patch("getpass.getpass")
    async def test_setup_api_keys_test_failure(self, mock_getpass, mock_input, mock_manager_class):
        """Test API key setup when key test fails."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # User wants to configure OpenAI
        mock_input.side_effect = ["y", "n", "n", "n"]
        mock_getpass.return_value = "sk-test-key-but-invalid"

        # Mock validation success but test failure
        mock_manager._validate_api_key.return_value = True
        mock_manager.test_api_key = AsyncMock(return_value=False)
        mock_manager.get_key.return_value = None

        # Run setup
        result = await setup_api_keys(interactive=True)

        # Should not store key that fails test
        assert "openai" not in result
        assert len(result) == 0
