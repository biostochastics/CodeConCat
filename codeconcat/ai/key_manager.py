"""Secure API key management for AI providers."""

import base64
import getpass
import json
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class KeyStorage(Enum):
    """Storage methods for API keys."""

    ENVIRONMENT = "environment"
    KEYRING = "keyring"
    ENCRYPTED_FILE = "encrypted_file"
    CONFIG_FILE = "config_file"


class APIKeyManager:
    """Manages API keys securely for AI providers."""

    _fernet: Optional[Fernet]

    def __init__(self, storage_method: KeyStorage = KeyStorage.ENCRYPTED_FILE):
        """Initialize the key manager.

        Args:
            storage_method: Method to use for storing keys
        """
        self.storage_method = storage_method
        self.config_dir = Path.home() / ".codeconcat"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.keys_file = self.config_dir / "api_keys.enc"
        self.salt_file = self.config_dir / "salt"
        self._fernet = None
        self._keys_cache: Dict[str, str] = {}

    def _get_or_create_salt(self) -> bytes:
        """Get or create a salt for key derivation."""
        if self.salt_file.exists():
            return self.salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
            # Set restrictive permissions
            self.salt_file.chmod(0o600)
            return salt

    def _get_master_password(self, confirm: bool = False) -> str:
        """Get master password from user."""
        password = getpass.getpass("Enter master password for API keys: ")
        if confirm:
            password2 = getpass.getpass("Confirm master password: ")
            if password != password2:
                raise ValueError("Passwords do not match")
        return password

    def _get_fernet(self, password: Optional[str] = None) -> Fernet:
        """Get Fernet instance for encryption/decryption."""
        if self._fernet is not None:
            return self._fernet

        if not password:
            password = self._get_master_password()

        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # Updated to OWASP 2023 recommendation
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._fernet = Fernet(key)
        return self._fernet

    def _validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate API key format and basic requirements.

        Args:
            provider: Provider name (openai, anthropic, etc.)
            api_key: API key to validate

        Returns:
            True if key appears valid
        """
        if not api_key or len(api_key) < 10:
            return False

        # Provider-specific validation
        validations = {
            "openai": lambda k: k.startswith(("sk-", "sess-")),
            "anthropic": lambda k: k.startswith("sk-ant-"),
            "openrouter": lambda k: k.startswith("sk-or-"),
        }

        if provider in validations:
            return bool(validations[provider](api_key))

        # Generic validation for unknown providers
        return len(api_key) >= 20

    async def test_api_key(self, provider: str, api_key: str) -> bool:
        """Test if an API key works by making a minimal request.

        Args:
            provider: Provider name
            api_key: API key to test

        Returns:
            True if key works
        """
        from .base import AIProviderConfig, AIProviderType
        from .factory import get_ai_provider

        try:
            # Map provider name to enum
            provider_map = {
                "openai": AIProviderType.OPENAI,
                "anthropic": AIProviderType.ANTHROPIC,
                "openrouter": AIProviderType.OPENROUTER,
                "ollama": AIProviderType.OLLAMA,
            }

            if provider not in provider_map:
                return False

            # Create minimal config
            config = AIProviderConfig(
                provider_type=provider_map[provider], api_key=api_key, max_tokens=1
            )

            # Try to create provider and validate
            provider_instance = get_ai_provider(config)
            result = await provider_instance.validate_connection()
            await provider_instance.close()
            return result

        except Exception:
            return False

    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider.

        Args:
            provider: Provider name (openai, anthropic, etc.)

        Returns:
            API key or None if not found
        """
        # Check cache first
        if provider in self._keys_cache:
            return self._keys_cache[provider]

        # Check environment variables
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "ollama": None,  # Ollama doesn't need API key
            "local_server": "LOCAL_LLM_API_KEY",
            "vllm": "VLLM_API_KEY",
            "lmstudio": "LMSTUDIO_API_KEY",
            "llamacpp_server": "LLAMACPP_SERVER_API_KEY",
        }

        if provider in env_vars and env_vars[provider]:
            env_var_name = env_vars[provider]
            if env_var_name:
                key = os.getenv(env_var_name)
                if key:
                    self._keys_cache[provider] = key
                    return key

        # Check encrypted file storage
        if self.storage_method == KeyStorage.ENCRYPTED_FILE:
            return self._get_key_from_encrypted_file(provider)

        # Check keyring storage
        if self.storage_method == KeyStorage.KEYRING:
            return self._get_key_from_keyring(provider)

        return None

    def _get_key_from_encrypted_file(self, provider: str) -> Optional[str]:
        """Get key from encrypted file storage."""
        if not self.keys_file.exists():
            return None

        try:
            fernet = self._get_fernet()
            encrypted_data = self.keys_file.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())

            key = keys.get(provider)
            if key:
                self._keys_cache[provider] = key
                return str(key)
            return None

        except Exception:
            return None

    def _get_key_from_keyring(self, provider: str) -> Optional[str]:
        """Get key from system keyring."""
        try:
            import keyring

            key = keyring.get_password("codeconcat", f"api_key_{provider}")
            if key:
                self._keys_cache[provider] = key
                return str(key)
            return None
        except ImportError:
            print("Warning: keyring module not installed. Install with: pip install keyring")
            return None
        except Exception:
            return None

    def set_key(self, provider: str, api_key: str, validate: bool = True) -> bool:
        """Store API key for a provider.

        Args:
            provider: Provider name
            api_key: API key to store
            validate: Whether to validate the key first

        Returns:
            True if stored successfully
        """
        # Validate format
        if validate and not self._validate_api_key(provider, api_key):
            raise ValueError(f"Invalid API key format for {provider}")

        # Store in cache
        self._keys_cache[provider] = api_key

        # Store persistently based on method
        if self.storage_method == KeyStorage.ENCRYPTED_FILE:
            return self._set_key_in_encrypted_file(provider, api_key)
        elif self.storage_method == KeyStorage.KEYRING:
            return self._set_key_in_keyring(provider, api_key)
        elif self.storage_method == KeyStorage.ENVIRONMENT:
            # Can't persist to environment, just cache
            return True

        return False

    def _set_key_in_encrypted_file(self, provider: str, api_key: str) -> bool:
        """Store key in encrypted file."""
        try:
            # Load existing keys or create new dict
            if self.keys_file.exists():
                fernet = self._get_fernet()
                encrypted_data = self.keys_file.read_bytes()
                decrypted_data = fernet.decrypt(encrypted_data)
                keys = json.loads(decrypted_data.decode())
            else:
                fernet = self._get_fernet(self._get_master_password(confirm=True))
                keys = {}

            # Update keys
            keys[provider] = api_key

            # Encrypt and save
            encrypted_data = fernet.encrypt(json.dumps(keys).encode())
            self.keys_file.write_bytes(encrypted_data)

            # Set restrictive permissions
            self.keys_file.chmod(0o600)

            return True

        except Exception as e:
            print(f"Error storing key: {e}")
            return False

    def _set_key_in_keyring(self, provider: str, api_key: str) -> bool:
        """Store key in system keyring."""
        try:
            import keyring

            keyring.set_password("codeconcat", f"api_key_{provider}", api_key)
            return True
        except ImportError:
            print("Error: keyring module not installed")
            return False
        except Exception as e:
            print(f"Error storing key in keyring: {e}")
            return False

    def delete_key(self, provider: str) -> bool:
        """Delete stored API key for a provider.

        Args:
            provider: Provider name

        Returns:
            True if deleted successfully
        """
        # Remove from cache
        if provider in self._keys_cache:
            del self._keys_cache[provider]

        # Delete from storage
        if self.storage_method == KeyStorage.ENCRYPTED_FILE:
            return self._delete_key_from_encrypted_file(provider)
        elif self.storage_method == KeyStorage.KEYRING:
            return self._delete_key_from_keyring(provider)

        return True

    def _delete_key_from_encrypted_file(self, provider: str) -> bool:
        """Delete key from encrypted file."""
        if not self.keys_file.exists():
            return True

        try:
            fernet = self._get_fernet()
            encrypted_data = self.keys_file.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)
            keys = json.loads(decrypted_data.decode())

            if provider in keys:
                del keys[provider]
                encrypted_data = fernet.encrypt(json.dumps(keys).encode())
                self.keys_file.write_bytes(encrypted_data)

            return True

        except Exception:
            return False

    def _delete_key_from_keyring(self, provider: str) -> bool:
        """Delete key from system keyring."""
        try:
            import keyring

            keyring.delete_password("codeconcat", f"api_key_{provider}")
            return True
        except Exception:
            return False

    def list_stored_providers(self) -> list[str]:
        """List providers with stored API keys.

        Returns:
            List of provider names
        """
        providers = []

        # Check environment
        for provider, env_var in [
            ("openai", "OPENAI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("openrouter", "OPENROUTER_API_KEY"),
        ]:
            if os.getenv(env_var):
                providers.append(f"{provider} (env)")

        # Check encrypted file
        if self.storage_method == KeyStorage.ENCRYPTED_FILE and self.keys_file.exists():
            try:
                fernet = self._get_fernet()
                encrypted_data = self.keys_file.read_bytes()
                decrypted_data = fernet.decrypt(encrypted_data)
                keys = json.loads(decrypted_data.decode())
                for provider in keys:
                    if provider not in providers:
                        providers.append(f"{provider} (encrypted)")
            except Exception:
                pass

        return providers


async def setup_api_keys(interactive: bool = True) -> Dict[str, str]:
    """Interactive setup for API keys.

    Args:
        interactive: Whether to prompt user for keys

    Returns:
        Dictionary of configured API keys
    """
    manager = APIKeyManager()
    configured_keys = {}

    print("\n🔑 API Key Configuration")
    print("=" * 50)

    providers = [
        ("openai", "OpenAI", "sk-..."),
        ("anthropic", "Anthropic", "sk-ant-..."),
        ("openrouter", "OpenRouter", "sk-or-..."),
    ]

    for provider_id, provider_name, key_format in providers:
        # Check if key already exists
        existing_key = manager.get_key(provider_id)

        if existing_key:
            print(f"✅ {provider_name}: Already configured")
            configured_keys[provider_id] = existing_key
            continue

        if not interactive:
            print(f"⚠️  {provider_name}: Not configured")
            continue

        # Ask user if they want to configure this provider
        response = input(f"\nConfigure {provider_name} API key? (y/n): ").lower()
        if response != "y":
            continue

        # Get API key from user
        print(f"Enter {provider_name} API key (format: {key_format})")
        api_key = getpass.getpass("API Key: ")

        if not api_key:
            print("⚠️  Skipped")
            continue

        # Validate and test
        if manager._validate_api_key(provider_id, api_key):
            print("✅ Valid format")

            # Test the key
            print("Testing API key...")
            is_valid = await manager.test_api_key(provider_id, api_key)

            if is_valid:
                print("✅ API key works!")
                # Store the key
                if manager.set_key(provider_id, api_key):
                    print("✅ Stored securely")
                    configured_keys[provider_id] = api_key
                else:
                    print("❌ Failed to store key")
            else:
                print("❌ API key test failed")
        else:
            print("❌ Invalid key format")

    print("\n" + "=" * 50)
    print(f"Configured providers: {len(configured_keys)}")
    for provider in configured_keys:
        print(f"  ✅ {provider}")

    return configured_keys


if __name__ == "__main__":
    import asyncio

    asyncio.run(setup_api_keys())
