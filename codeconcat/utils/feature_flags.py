"""
Feature Flags System for Gradual Rollout

This module provides a feature flag system to enable gradual rollout of new
features and fixes, allowing for safe deployment and easy rollback.
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status of a feature flag."""

    DISABLED = "disabled"
    ENABLED = "enabled"
    PARTIAL = "partial"  # Enabled for specific conditions
    CANARY = "canary"  # Enabled for a percentage of users


class FeatureFlags:
    """
    Centralized feature flag management system.

    Features can be controlled via:
    1. Environment variables (highest priority)
    2. Configuration file
    3. Default values (lowest priority)
    """

    # Default feature flags
    _defaults = {
        # Collector features
        "use_async_collectors": False,
        "use_collector_factory": True,
        "enable_collector_bridge": True,
        # Parser features
        "use_tree_sitter_parsers": True,
        "enable_parser_fallback": True,
        "enable_unicode_handler": False,
        "strict_parser_mode": False,
        # Security features
        "enable_path_validation": True,
        "enable_rate_limiting": False,
        "enable_input_sanitization": True,
        # Performance features
        "enable_streaming": False,
        "enable_connection_pooling": False,
        "enable_progress_indicators": True,
        # Configuration
        "use_unified_config": False,
        "enable_config_migration": True,
        # Error handling
        "enable_error_recovery": True,
        "enable_graceful_degradation": True,
        "verbose_error_messages": False,
        # Experimental features
        "enable_experimental_parsers": False,
        "enable_telemetry": False,
        "enable_canary_testing": False,
    }

    # Feature metadata (descriptions, risks, etc.)
    _metadata = {
        "use_async_collectors": {
            "description": "Use async collectors for remote sources",
            "risk": "medium",
            "rollout_percentage": 0,
        },
        "use_collector_factory": {
            "description": "Use factory pattern for collector creation",
            "risk": "low",
            "rollout_percentage": 100,
        },
        "enable_unicode_handler": {
            "description": "Enable universal unicode handling in parsers",
            "risk": "high",
            "rollout_percentage": 0,
        },
        "enable_rate_limiting": {
            "description": "Enable rate limiting on API endpoints",
            "risk": "low",
            "rollout_percentage": 0,
        },
        "use_unified_config": {
            "description": "Use new unified configuration system",
            "risk": "high",
            "rollout_percentage": 0,
        },
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize feature flags.

        Args:
            config_file: Optional path to feature flags config file
        """
        self._flags = self._defaults.copy()
        self._config_file = config_file
        self._overrides: Dict[str, bool] = {}
        self._canary_cache: Dict[str, bool] = {}

        # Load from config file if provided
        if config_file and config_file.exists():
            self._load_from_file(config_file)

        # Override with environment variables
        self._load_from_env()

    def _load_from_file(self, config_file: Path):
        """Load feature flags from configuration file."""
        try:
            with open(config_file) as f:
                config = json.load(f)
                self._flags.update(config.get("flags", {}))
                self._metadata.update(config.get("metadata", {}))
                logger.info(f"Loaded feature flags from {config_file}")
        except Exception as e:
            logger.error(f"Error loading feature flags from {config_file}: {e}")

    def _load_from_env(self):
        """Load feature flags from environment variables."""
        prefix = "CODECONCAT_FEATURE_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                flag_name = key[len(prefix) :].lower()
                if flag_name in self._flags:
                    # Parse boolean values
                    if value.lower() in ("true", "1", "yes", "on"):
                        self._flags[flag_name] = True
                    elif value.lower() in ("false", "0", "no", "off"):
                        self._flags[flag_name] = False
                    else:
                        # For non-boolean strings, treat as truthy if not empty
                        self._flags[flag_name] = bool(value.strip())
                    logger.debug(f"Override flag {flag_name} from env: {self._flags[flag_name]}")

    def is_enabled(self, flag_name: str, context: Optional[Dict] = None) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag
            context: Optional context for conditional flags

        Returns:
            True if the feature is enabled
        """
        # Check overrides first
        if flag_name in self._overrides:
            override_val = self._overrides[flag_name]
            return bool(override_val)

        # Check if flag exists
        if flag_name not in self._flags:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False

        value = self._flags[flag_name]

        # Handle different value types
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            # Check for special values
            if value == "canary":
                return self._check_canary(flag_name, context)
            elif value == "partial":
                return self._check_partial(flag_name, context)
        elif isinstance(value, (int, float)):
            # Percentage-based rollout
            return self._check_percentage(flag_name, value, context)

        return bool(value)

    def _check_canary(self, flag_name: str, context: Optional[Dict]) -> bool:
        """Check if canary testing should enable this flag."""
        if not context:
            return False

        # Check if this context is in canary group
        cache_key = f"{flag_name}:{context.get('user_id', 'anonymous')}"
        if cache_key in self._canary_cache:
            return self._canary_cache[cache_key]

        # Determine canary status (e.g., based on user ID hash)
        metadata = self._metadata.get(flag_name, {})
        percentage_val = metadata.get("rollout_percentage", 0)
        # Ensure percentage is a number
        try:
            if isinstance(percentage_val, (int, float, str)):
                percentage = float(percentage_val)
            else:
                percentage = 0.0
        except (TypeError, ValueError):
            percentage = 0.0

        if context.get("user_id"):
            # Use consistent hashing for user
            # Use consistent hashing for user
            user_hash = hash(context["user_id"]) % 100
            is_canary = user_hash < percentage
        else:
            # Random for anonymous
            import random

            # Random for anonymous
            rand_val = random.random() * 100
            is_canary = rand_val < percentage

        self._canary_cache[cache_key] = is_canary
        return is_canary

    def _check_partial(self, flag_name: str, context: Optional[Dict]) -> bool:
        """Check if partial rollout conditions are met."""
        if not context:
            return False

        metadata = self._metadata.get(flag_name, {})
        conditions = metadata.get("conditions", {})

        # Check all conditions
        # Check all conditions with proper typing
        if not isinstance(conditions, dict):
            return False
        # Ensure we return a bool
        result = all(context.get(key) == expected for key, expected in conditions.items())
        return bool(result)

    def _check_percentage(self, flag_name: str, percentage: float, context: Optional[Dict]) -> bool:
        """Check percentage-based rollout."""
        if context and context.get("user_id"):
            # Consistent for users
            return hash(f"{flag_name}:{context['user_id']}") % 100 < percentage
        else:
            # Random for anonymous
            import random

            return random.random() * 100 < percentage

    def set_override(self, flag_name: str, value: bool):
        """
        Temporarily override a feature flag.

        Args:
            flag_name: Name of the flag to override
            value: Override value
        """
        self._overrides[flag_name] = value
        logger.info(f"Override set for {flag_name}: {value}")

    def clear_override(self, flag_name: str):
        """
        Clear an override for a feature flag.

        Args:
            flag_name: Name of the flag to clear override for
        """
        if flag_name in self._overrides:
            del self._overrides[flag_name]
            logger.info(f"Override cleared for {flag_name}")

    def get_all_flags(self) -> Dict[str, Any]:
        """Get all current flag values."""
        result = self._flags.copy()
        result.update(self._overrides)
        return result

    def get_metadata(self, flag_name: str) -> Dict[str, Any]:
        """Get metadata for a specific flag."""
        return self._metadata.get(flag_name, {})

    def save_to_file(self, config_file: Path):
        """Save current flags to a configuration file."""
        try:
            config = {
                "flags": self._flags,
                "metadata": self._metadata,
                "saved_at": datetime.now().isoformat(),
            }
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved feature flags to {config_file}")
        except Exception as e:
            logger.error(f"Error saving feature flags to {config_file}: {e}")

    def with_flag(self, flag_name: str, enabled: bool = True):
        """
        Decorator to conditionally execute code based on feature flag.

        Args:
            flag_name: Name of the feature flag
            enabled: Expected flag state
        """

        def decorator(func: Callable) -> Callable:
            """Enhances a function with conditional execution based on a feature flag.
            Parameters:
                - func (Callable): The function to be wrapped by the decorator.
            Returns:
                - Callable: A new function that executes conditionally based on a feature flag."""
            def wrapper(*args, **kwargs):
                if self.is_enabled(flag_name) == enabled:
                    return func(*args, **kwargs)
                else:
                    logger.debug(f"Skipping {func.__name__} - flag {flag_name} is {not enabled}")
                    return None

            return wrapper

        return decorator

    def choose(
        self, flag_name: str, if_enabled: Any, if_disabled: Any, context: Optional[Dict] = None
    ) -> Any:
        """
        Choose a value based on feature flag state.

        Args:
            flag_name: Name of the feature flag
            if_enabled: Value to return if flag is enabled
            if_disabled: Value to return if flag is disabled
            context: Optional context for conditional flags

        Returns:
            The chosen value based on flag state
        """
        if self.is_enabled(flag_name, context):
            return if_enabled
        else:
            return if_disabled


# Global instance
_flags = FeatureFlags()


# Convenience functions
def is_enabled(flag_name: str, context: Optional[Dict] = None) -> bool:
    """Check if a feature flag is enabled."""
    return _flags.is_enabled(flag_name, context)


def set_override(flag_name: str, value: bool):
    """Temporarily override a feature flag."""
    _flags.set_override(flag_name, value)


def clear_override(flag_name: str):
    """Clear an override for a feature flag."""
    _flags.clear_override(flag_name)


def with_flag(flag_name: str, enabled: bool = True):
    """Decorator to conditionally execute code based on feature flag."""
    return _flags.with_flag(flag_name, enabled)


def choose(
    flag_name: str, if_enabled: Any, if_disabled: Any, context: Optional[Dict] = None
) -> Any:
    """Choose a value based on feature flag state."""
    return _flags.choose(flag_name, if_enabled, if_disabled, context)


def get_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    return _flags
