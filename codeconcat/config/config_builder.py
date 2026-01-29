"""
Configuration builder for CodeConCat.

This module provides a builder pattern implementation for loading and managing
CodeConCat configuration from multiple sources in a clearly defined order:
1. Defaults (from the Pydantic model)
2. Presets (lean, medium, full output configurations)
3. YAML configuration file
4. CLI argument overrides

Each stage builds upon the previous, and configuration sources are strictly applied
in this order, making it clear where each setting comes from.
"""

import logging
import os
from enum import Enum
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from codeconcat.base_types import CodeConCatConfig
from codeconcat.errors import ConfigurationError

from ..constants import DEFAULT_EXCLUDE_PATTERNS

logger = logging.getLogger(__name__)

# Define settings for each output preset
PRESET_CONFIGS = {
    "lean": {
        "disable_ai_context": True,
        "include_repo_overview": False,
        "parser_engine": "regex",  # New name for disable_tree=True
        "include_file_index": False,
        "include_file_summary": False,
        "remove_comments": True,  # Keep aggressive cleaning for lean
        "remove_docstrings": True,
        "remove_empty_lines": True,
        "include_declarations_in_summary": False,  # Implied by include_file_summary=False
        "include_imports_in_summary": False,  # Implied by include_file_summary=False
        "include_tokens_in_summary": False,  # Implied by include_file_summary=False
        "include_security_in_summary": False,  # Implied by include_file_summary=False
    },
    "medium": {
        "disable_ai_context": False,
        "include_repo_overview": True,
        "parser_engine": "tree_sitter",  # New name for disable_tree=False
        "include_file_index": True,
        "include_file_summary": True,
        "remove_comments": False,  # Less aggressive cleaning for medium
        "remove_docstrings": False,
        "remove_empty_lines": False,
        "include_declarations_in_summary": True,
        "include_imports_in_summary": False,  # Keep imports off by default for medium
        "include_tokens_in_summary": True,
        "include_security_in_summary": True,
    },
    "full": {
        "disable_ai_context": False,
        "include_repo_overview": True,
        "parser_engine": "tree_sitter",  # New name for disable_tree=False
        "include_file_index": True,
        "include_file_summary": True,
        "remove_comments": False,  # Minimal cleaning for full
        "remove_docstrings": False,
        "remove_empty_lines": False,
        "include_declarations_in_summary": True,
        "include_imports_in_summary": True,  # Include imports for full
        "include_tokens_in_summary": True,
        "include_security_in_summary": True,
    },
}


class ConfigSource(Enum):
    """Enum representing the source of a configuration setting."""

    DEFAULT = "default"
    PRESET = "preset"
    YAML = "yaml"
    CLI = "cli"
    COMPUTED = "computed"  # For values derived during processing


class ConfigSetting:
    """Class representing a single configuration setting with its source and value."""

    def __init__(self, name: str, value: Any, source: ConfigSource):
        self.name = name
        self.value = value
        self.source = source

    def __repr__(self) -> str:
        return f"ConfigSetting(name={self.name}, value={self.value}, source={self.source.value})"


class ConfigBuilder:
    """
    Builder class for CodeConCat configuration that processes sources in a strict order.

    This class follows the builder pattern to construct a configuration object through
    a series of well-defined steps:
    1. Start with default values from the Pydantic model
    2. Apply preset configuration (lean, medium, full)
    3. Load and apply YAML configuration file
    4. Apply CLI arguments as final overrides

    The builder tracks the source of each configuration setting, allowing for detailed
    reporting on where each value came from.
    """

    def __init__(self):
        """Initialize the ConfigBuilder with empty configuration."""
        self._config_dict: dict[str, Any] = {}
        self._sources: dict[str, ConfigSource] = {}
        self._initialized = False

        # Store raw values from each source for reference
        self._preset_values: dict[str, Any] = {}
        self._yaml_values: dict[str, Any] = {}
        self._cli_values: dict[str, Any] = {}

    def with_defaults(self) -> "ConfigBuilder":
        """
        Initialize with default values from the Pydantic model.

        This is the first step in the configuration process, setting up the base
        configuration with defaults defined in the CodeConCatConfig model.

        Returns:
            Self, to enable method chaining.
        """
        # Create a default instance of the config model to extract default values
        default_config = CodeConCatConfig.model_validate({})

        # Extract default values as a dictionary
        config_dict = default_config.model_dump()

        # Set use_default_excludes to True by default if not explicitly set
        if "use_default_excludes" not in config_dict or config_dict["use_default_excludes"] is None:
            config_dict["use_default_excludes"] = True

        # Initialize our configuration dictionary with these defaults
        self._config_dict = config_dict

        # Record the source for each setting
        self._sources = dict.fromkeys(config_dict.keys(), ConfigSource.DEFAULT)

        # Mark as initialized
        self._initialized = True

        logger.debug("Initialized configuration with defaults")
        return self

    def with_preset(self, preset_name: str = "medium") -> "ConfigBuilder":
        """
        Apply a named preset configuration.

        Presets provide predefined combinations of settings optimized for different
        use cases (lean, medium, full).

        Args:
            preset_name: Name of the preset to apply ("lean", "medium", or "full").
                         Defaults to "medium".

        Returns:
            Self, to enable method chaining.

        Raises:
            ConfigurationError: If an unknown preset is specified.
        """
        if not self._initialized:
            self.with_defaults()

        # Validate the preset name
        if preset_name not in PRESET_CONFIGS:
            valid_presets = ", ".join(PRESET_CONFIGS.keys())
            raise ConfigurationError(
                f"Unknown preset '{preset_name}'. Valid presets are: {valid_presets}"
            )

        # Store the preset values for reference
        self._preset_values = PRESET_CONFIGS[preset_name].copy()

        # Handle compatibility with old flag names
        if "parser_engine" in self._preset_values:
            parser_engine = self._preset_values.pop("parser_engine")
            # Convert new parser_engine to old disable_tree flag for backward compatibility
            self._preset_values["disable_tree"] = parser_engine != "tree_sitter"

        # Apply preset values, overriding defaults
        for key, value in self._preset_values.items():
            self._config_dict[key] = value
            self._sources[key] = ConfigSource.PRESET

        logger.debug(f"Applied '{preset_name}' preset configuration")
        return self

    def with_yaml_config(self, config_path: str | None = None) -> "ConfigBuilder":
        """
        Load and apply configuration from a YAML file.

        This step looks for a .codeconcat.yml file in the current directory by default,
        or uses a custom path if specified.

        Args:
            config_path: Optional path to a YAML configuration file. If not provided,
                         searches for .codeconcat.yml in the current directory.

        Returns:
            Self, to enable method chaining.

        Raises:
            ConfigurationError: If the config file exists but cannot be loaded.
        """
        if not self._initialized:
            self.with_defaults()

        # Determine the configuration path
        if config_path is None:
            config_path = os.path.join(os.getcwd(), ".codeconcat.yml")

        # Check if the config file exists
        if not os.path.exists(config_path):
            logger.debug(f"No configuration file found at {config_path}, skipping YAML config")
            return self

        # Load YAML configuration
        try:
            with open(config_path, encoding="utf-8") as file:
                yaml_config = yaml.safe_load(file) or {}

            # Handle compatibility with old flag names
            if yaml_config.get("parser_engine"):
                parser_engine = yaml_config.pop("parser_engine")
                # Convert new parser_engine to old disable_tree flag for backward compatibility
                yaml_config["disable_tree"] = parser_engine != "tree_sitter"

            # Store the YAML values for reference
            self._yaml_values = yaml_config.copy()

            # Apply YAML config values, overriding defaults and presets
            for key, value in yaml_config.items():
                self._config_dict[key] = value
                self._sources[key] = ConfigSource.YAML

            logger.debug(f"Loaded configuration from {config_path}")
        except yaml.YAMLError as e:
            error_msg = f"Error parsing YAML configuration file at {config_path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e
        except Exception as e:
            error_msg = f"Error loading configuration file at {config_path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

        return self

    def with_cli_args(self, cli_args: dict[str, Any]) -> "ConfigBuilder":
        """
        Apply command-line arguments as final configuration overrides.

        CLI arguments have the highest precedence and will override any previous settings.

        Args:
            cli_args: Dictionary of command-line arguments to apply.

        Returns:
            Self, to enable method chaining.
        """
        if not self._initialized:
            self.with_defaults()

        # Map CLI argument names to config field names
        # This handles cases where CLI args use different naming than config fields
        # or where transformations need to be applied
        cli_to_config_map = {
            # Basic flag conversions
            "disable_tree": "disable_tree",  # Direct mapping
            "no_tree": "disable_tree",  # Map no_tree to disable_tree
            "no_ai_context": "disable_ai_context",  # no_X maps to disable_X
            "no_annotations": "disable_annotations",
            "no_symbols": "disable_symbols",
            "no_progress_bar": "disable_progress_bar",
            # Output settings
            "output": "output",
            "format": "format",
            # Compression settings
            "enable_compression": "enable_compression",
            "compression_level": "compression_level",
            "compression_placeholder": "compression_placeholder",
            "compression_keep_threshold": "compression_keep_threshold",
            "compression_keep_tags": "compression_keep_tags",
            # Other direct mappings
            "preset": "preset",
            "parser_engine": "parser_engine",
            "sort_files": "sort_files",
            "docs": "extract_docs",
            "merge_docs": "merge_docs",
            "remove_docstrings": "remove_docstrings",
            "cross_link_symbols": "cross_link_symbols",
            "max_workers": "max_workers",
            "split_output": "split_output",
        }

        # Prepare processed CLI values
        processed_cli_values = {}

        # Process each CLI argument that has a value (not None)
        for cli_key, cli_value in cli_args.items():
            if cli_value is None:
                continue

            # Check if this CLI argument maps to a config field
            config_key = cli_to_config_map.get(cli_key)

            if config_key:
                # Store in processed values with the correct config field name
                processed_cli_values[config_key] = cli_value
            elif cli_key in CodeConCatConfig.model_fields:
                # If CLI key is already a valid config field (direct match)
                processed_cli_values[cli_key] = cli_value

        # Store processed values for use in debugging
        self._cli_values = processed_cli_values

        # Apply compatibility fixes and special handling
        if "parser_engine" in processed_cli_values:
            parser_engine = processed_cli_values.pop("parser_engine")
            # Only set disable_tree if parser_engine was actually provided (not empty)
            if parser_engine:  # Skip empty strings from CLI when option is None
                # Convert new parser_engine to old disable_tree flag for backward compatibility
                processed_cli_values["disable_tree"] = parser_engine != "tree_sitter"

        # Apply CLI args, overriding all previous settings
        for key, value in processed_cli_values.items():
            if key in CodeConCatConfig.model_fields:
                self._config_dict[key] = value
                self._sources[key] = ConfigSource.CLI

        logger.debug(f"Applied CLI overrides: {processed_cli_values}")
        return self

    def _finalize_paths(self) -> None:
        """
        Finalize path-related configuration settings.

        Handles special processing for paths, including:
        - Ensuring target_path is absolute
        - Setting default output path based on format
        - Processing exclude_paths
        - Setting default include_paths for local and GitHub sources
        """
        # Ensure target_path is absolute
        if "target_path" in self._config_dict:
            target_path = self._config_dict["target_path"]
            if target_path and not os.path.isabs(target_path):
                absolute_path = os.path.abspath(target_path)
                self._config_dict["target_path"] = absolute_path
                self._sources["target_path"] = ConfigSource.COMPUTED

        # Only set default output path if it wasn't provided by any source
        # Don't override CLI or YAML specified output paths
        if self._sources.get("output") == ConfigSource.DEFAULT and self._config_dict.get(
            "output"
        ) in ("code_concat_output.md", ""):
            # Clear to empty so main.py generates the dated default name
            self._config_dict["output"] = ""
            self._sources["output"] = ConfigSource.COMPUTED

        # Apply default exclude patterns if not overridden
        if (
            "use_default_excludes" in self._config_dict
            and self._config_dict["use_default_excludes"] is True
        ):
            # Ensure current_excludes is always a list even if None
            current_excludes = self._config_dict.get("exclude_paths", []) or []
            # Only add default exclusions if they're not already specified
            default_excludes = [
                pattern for pattern in DEFAULT_EXCLUDE_PATTERNS if pattern not in current_excludes
            ]
            self._config_dict["exclude_paths"] = current_excludes + default_excludes
            self._sources["exclude_paths"] = ConfigSource.COMPUTED

        # Set up include paths for both local and remote sources
        if "include_paths" not in self._config_dict or not self._config_dict["include_paths"]:
            # Default include patterns for common code files
            lang_includes = [
                # Common code files
                "**/*.py",  # Python
                "**/*.js",
                "**/*.jsx",
                "**/*.ts",
                "**/*.tsx",  # JavaScript/TypeScript
                "**/*.java",
                "**/*.kt",
                "**/*.scala",  # JVM
                "**/*.rb",
                "**/*.rake",
                "**/*.erb",  # Ruby
                "**/*.go",  # Go
                "**/*.rs",  # Rust
                "**/*.c",
                "**/*.cpp",
                "**/*.h",
                "**/*.hpp",  # C/C++
                "**/*.cs",  # C#
                "**/*.php",  # PHP
                "**/*.r",
                "**/*.R",  # R
                "**/*.swift",  # Swift
                "**/*.lua",  # Lua
                "**/*.jl",  # Julia
                "**/*.sh",
                "**/*.bash",  # Shell
                # Common project files
                "**/README*",
                "**/LICENSE*",
                "**/CHANGELOG*",
                "**/pyproject.toml",
                "**/setup.py",
                "**/package.json",
                "**/requirements.txt",
                "**/Makefile",
                "**/Dockerfile",
            ]

            # Apply special handling for remote repos vs local
            if "source_url" in self._config_dict and self._config_dict["source_url"]:
                # For GitHub, prioritize commonly structured directories
                js_patterns = [
                    "src/**/*.ts",
                    "src/**/*.tsx",
                    "src/**/*.js",
                    "src/**/*.jsx",
                    "app/**/*.ts",
                    "app/**/*.tsx",
                    "app/**/*.js",
                    "app/**/*.jsx",
                    "components/**/*.ts",
                    "components/**/*.tsx",
                    "components/**/*.js",
                    "components/**/*.jsx",
                    "lib/**/*.ts",
                    "lib/**/*.tsx",
                    "lib/**/*.js",
                    "lib/**/*.jsx",
                ]
                lang_includes.extend(js_patterns)

            # Set the computed include_paths
            self._config_dict["include_paths"] = lang_includes
            self._sources["include_paths"] = ConfigSource.COMPUTED

    def build(self) -> CodeConCatConfig:
        """
        Build and validate the final configuration object.

        This method finalizes special configuration settings (like paths),
        validates the configuration, and returns a completed CodeConCatConfig object.

        Returns:
            A validated CodeConCatConfig object.

        Raises:
            ConfigurationError: If validation fails.
        """
        if not self._initialized:
            self.with_defaults()

        # Perform special processing for paths and defaults
        self._finalize_paths()

        try:
            # Validate the final dictionary using the Pydantic model
            logger.debug(f"Final config dict before validation: {self._config_dict}")
            validated_config = CodeConCatConfig(**self._config_dict)
            logger.debug(f"Validated Config: {validated_config}")
            return validated_config
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

    def get_config_details(self) -> dict[str, ConfigSetting]:
        """
        Get detailed information about configuration settings and their sources.

        This method is useful for debugging and transparency, showing where each
        configuration value came from.

        Returns:
            Dictionary mapping setting names to ConfigSetting objects.
        """
        return {
            name: ConfigSetting(name, self._config_dict[name], source)
            for name, source in self._sources.items()
        }

    def print_config_details(self) -> None:
        """
        Print a formatted report of configuration settings and their sources.

        This is a convenience method for displaying configuration details to the user.
        """
        print("\nConfiguration Details:")
        print("======================")

        # Group settings by source for more readable output
        source_groups: dict[ConfigSource, list[str]] = {source: [] for source in ConfigSource}

        for name, source in self._sources.items():
            source_groups[source].append(name)

        # Print settings grouped by source
        for source in ConfigSource:
            settings = source_groups[source]
            if not settings:
                continue

            print(f"\n{source.value.upper()} settings:")
            print("-" * (len(source.value) + 10))

            for name in sorted(settings):
                value = self._config_dict[name]
                # Format output for readability
                if isinstance(value, list | tuple) and len(value) > 3:
                    value_str = (
                        f"[{', '.join(str(v) for v in value[:3])}... +{len(value) - 3} more]"
                    )
                else:
                    value_str = str(value)

                # Truncate very long values
                if len(value_str) > 70:
                    value_str = value_str[:67] + "..."

                print(f"  {name}: {value_str}")

        print("\n")


def load_config(
    cli_args: dict[str, Any], config_path_override: str | None = None
) -> CodeConCatConfig:
    """
    Load and build configuration using the new ConfigBuilder class.

    This is a compatibility wrapper for the old load_config function to ensure
    a smooth transition to the new builder pattern.

    Args:
        cli_args: Dictionary of command-line arguments.
        config_path_override: Optional path to a YAML configuration file.

    Returns:
        A validated CodeConCatConfig object.

    Raises:
        ConfigurationError: If configuration loading or validation fails.
    """
    # Extract preset name from CLI args or use default
    preset_name = cli_args.get("output_preset", "medium")

    # Handle legacy flag conversion
    if "parser_engine" not in cli_args and "disable_tree" in cli_args:
        disable_tree = cli_args.get("disable_tree")
        if disable_tree is not None:
            # Convert disable_tree to parser_engine
            cli_args["parser_engine"] = "regex" if disable_tree else "tree_sitter"

    # Build configuration in strict order
    try:
        builder = ConfigBuilder()
        config = (
            builder.with_defaults()
            .with_preset(preset_name)
            .with_yaml_config(config_path_override)
            .with_cli_args(cli_args)
            .build()
        )

        # Print configuration details if requested
        if cli_args.get("show_config_detail"):
            builder.print_config_details()

        return config
    except Exception as e:
        raise ConfigurationError(f"Failed to build configuration: {e}") from e
