"""
Global state and configuration management for the CLI.

This module provides a singleton pattern for managing global application state
across different CLI commands. It uses Pydantic for data validation and ensures
type safety for configuration objects.

The global state includes:
- Verbosity settings for logging
- Quiet mode flag for output suppression
- Configuration file path
- Parsed configuration object

Usage:
    from codeconcat.cli.config import get_state, set_config

    state = get_state()
    state.verbose = 2  # Set debug verbosity

    config = CodeConCatConfig(...)
    set_config(config)
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from codeconcat.base_types import CodeConCatConfig


class GlobalState(BaseModel):
    """
    Global state container for CLI settings.

    This Pydantic model serves as a centralized state management system
    for the CLI application. It maintains settings that need to be accessed
    across different commands and modules.

    Attributes:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)
        quiet: Flag to suppress all non-error output
        config_path: Path to the configuration file if provided
        config: Parsed CodeConCatConfig object if loaded

    Note:
        Uses Pydantic's BaseModel for automatic validation and serialization.
        The model_config enables arbitrary types to allow Path objects.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    verbose: int = 0
    quiet: bool = False
    config_path: Path | None = None
    config: CodeConCatConfig | None = None


# Singleton instance - ensures only one state object exists globally
# This pattern allows state sharing across all CLI commands without passing objects
_state = GlobalState()


def get_state() -> GlobalState:
    """
    Get the global state instance.

    Returns the singleton GlobalState instance that maintains CLI settings
    across the application lifecycle.

    Returns:
        GlobalState: The singleton state instance

    Example:
        >>> state = get_state()
        >>> print(f"Verbosity: {state.verbose}")
        >>> if state.config:
        ...     print(f"Config loaded from: {state.config_path}")

    Note:
        This function always returns the same instance, implementing
        the singleton pattern for global state management.
    """
    return _state


def set_config(config: CodeConCatConfig) -> None:
    """
    Set the global configuration.

    Updates the global state with a parsed configuration object.
    This is typically called after loading and validating a configuration
    file or after building a configuration from CLI arguments.

    Args:
        config: A validated CodeConCatConfig object containing all
                application settings

    Example:
        >>> from codeconcat.base_types import CodeConCatConfig
        >>> config = CodeConCatConfig.from_yaml(".codeconcat.yml")
        >>> set_config(config)
        >>> # Config is now available globally via get_state().config

    Note:
        This modifies the singleton state instance, making the configuration
        available to all parts of the application.
    """
    _state.config = config
