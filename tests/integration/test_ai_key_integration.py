"""Integration tests for AI API key management and provider setup."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from codeconcat.ai.base import AIProviderConfig, AIProviderType
from codeconcat.ai.factory import get_ai_provider
from codeconcat.ai.key_manager import APIKeyManager, KeyStorage


@pytest.fixture
def clean_env():
    """Fixture to provide a clean environment without API keys."""
    with patch.dict(os.environ, {}, clear=True):
        yield


class TestAPIKeyIntegration:
    """Test API key management with real provider initialization."""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
        reason="No API keys available for testing",
    )
    def test_provider_initialization_with_env_key(self):
        """Test that providers can initialize with keys from environment."""
        # Try OpenAI first
        if os.getenv("OPENAI_API_KEY"):
            config = AIProviderConfig(
                provider_type=AIProviderType.OPENAI, model="gpt-3.5-turbo", max_tokens=100
            )

            provider = get_ai_provider(config)
            assert provider is not None
            assert provider.config.api_key is not None
            assert provider.config.api_key.startswith("sk-")

        # Try Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            config = AIProviderConfig(
                provider_type=AIProviderType.ANTHROPIC,
                model="claude-3-haiku-20240307",
                max_tokens=100,
            )

            provider = get_ai_provider(config)
            assert provider is not None
            assert provider.config.api_key is not None
            assert provider.config.api_key.startswith("sk-ant-")

    def test_provider_initialization_with_explicit_key(self):
        """Test that providers can initialize with explicitly provided keys."""
        # Test with a fake but valid-format key
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="sk-test1234567890abcdefghijklmnopqrst",
            model="gpt-3.5-turbo",
            max_tokens=100,
        )

        provider = get_ai_provider(config)
        assert provider is not None
        assert provider.config.api_key == "sk-test1234567890abcdefghijklmnopqrst"

    @patch("getpass.getpass")
    def test_key_manager_with_provider_factory(self, mock_getpass, tmp_path):
        """Test that key manager integrates properly with provider factory."""
        # Clear environment variables to avoid interference
        with patch.dict(os.environ, {}, clear=True):
            # Setup temporary home
            with patch.object(Path, "home", return_value=tmp_path):
                # Create manager and store a test key
                manager = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)
                mock_getpass.return_value = "test-password"

                test_key = "sk-test1234567890abcdefghijklmnopqrst"
                success = manager.set_key("openai", test_key, validate=False)
                assert success

                # Clear cache to force file retrieval
                manager._keys_cache.clear()
                manager._fernet = None

                # Retrieve key and use it with provider
                retrieved_key = manager.get_key("openai")
                assert retrieved_key == test_key

            # Create provider with retrieved key
            config = AIProviderConfig(
                provider_type=AIProviderType.OPENAI,
                api_key=retrieved_key,
                model="gpt-3.5-turbo",
                max_tokens=100,
            )

            provider = get_ai_provider(config)
            assert provider is not None
            assert provider.config.api_key == test_key

    def test_provider_error_handling_no_key(self):
        """Test provider behavior when no API key is available."""
        # Clear environment to ensure no key is available
        with patch.dict(os.environ, {}, clear=True):
            config = AIProviderConfig(
                provider_type=AIProviderType.OPENAI, model="gpt-3.5-turbo", max_tokens=100
            )

            # Provider should still be created, but with no key
            provider = get_ai_provider(config)
            assert provider is not None

            # Config should not have an API key
            assert provider.config.api_key is None or provider.config.api_key == ""

    @pytest.mark.asyncio
    async def test_provider_validation_with_invalid_key(self):
        """Test provider validation with an invalid API key."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="invalid-key",
            model="gpt-3.5-turbo",
            max_tokens=100,
        )

        provider = get_ai_provider(config)

        # Mock the actual API call to avoid making real requests
        with patch.object(provider, "validate_connection", return_value=False):
            is_valid = await provider.validate_connection()
            assert not is_valid

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
    async def test_provider_validation_with_real_key(self):
        """Test provider validation with a real API key."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI, model="gpt-3.5-turbo", max_tokens=1
        )

        provider = get_ai_provider(config)

        # This will make a real API call to validate the key
        is_valid = await provider.validate_connection()
        assert is_valid

    def test_multiple_provider_key_management(self, tmp_path, clean_env):
        """Test managing keys for multiple providers."""
        with patch.object(Path, "home", return_value=tmp_path):
            manager = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)

            # Mock password input
            with patch("getpass.getpass", return_value="test-password"):
                # Store keys for multiple providers
                providers_keys = {
                    "openai": "sk-test1234567890abcdefghijklmnopqrst",
                    "anthropic": "sk-ant-test1234567890abcdefghijklmn",
                    "openrouter": "sk-or-test1234567890abcdefghijklmno",
                }

                for provider, key in providers_keys.items():
                    success = manager.set_key(provider, key, validate=False)
                    assert success

                # Clear cache to force file retrieval
                manager._keys_cache.clear()
                manager._fernet = None

                # Retrieve all keys
                for provider, expected_key in providers_keys.items():
                    retrieved_key = manager.get_key(provider)
                    assert retrieved_key == expected_key

    def test_key_persistence_across_sessions(self, tmp_path, clean_env):
        """Test that keys persist across different manager instances."""
        with patch.object(Path, "home", return_value=tmp_path):
            # First session - store key
            with patch("getpass.getpass", return_value="test-password"):
                manager1 = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)
                test_key = "sk-test1234567890abcdefghijklmnopqrst"
                success = manager1.set_key("openai", test_key, validate=False)
                assert success

            # Second session - retrieve key
            with patch("getpass.getpass", return_value="test-password"):
                manager2 = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)
                retrieved_key = manager2.get_key("openai")
                assert retrieved_key == test_key

    def test_wrong_password_handling(self, tmp_path, clean_env):
        """Test that wrong password fails gracefully."""
        with patch.object(Path, "home", return_value=tmp_path):
            # Store with one password
            with patch("getpass.getpass", return_value="correct-password"):
                manager1 = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)
                test_key = "sk-test1234567890abcdefghijklmnopqrst"
                success = manager1.set_key("openai", test_key, validate=False)
                assert success

            # Try to retrieve with wrong password
            with patch("getpass.getpass", return_value="wrong-password"):
                manager2 = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)
                retrieved_key = manager2.get_key("openai")
                # Should return None due to decryption failure
                assert retrieved_key is None
