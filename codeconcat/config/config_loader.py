import logging
import os
from typing import Any, Dict, Optional
import yaml
from pydantic import ValidationError

from codeconcat.base_types import CodeConCatConfig

# Common directories and files to exclude by default
DEFAULT_EXCLUDE_PATTERNS = [
    # Version Control
    ".git",
    ".svn",
    ".hg",
    # Python Virtual Environments
    "venv",
    ".venv",
    "env",
    ".env",
    "*env",  # General pattern for envs
    # Python Cache/Build
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    "*.egg-info",
    # Node.js
    "node_modules",
    # IDE/Editor specific
    ".vscode",
    ".idea",
    # OS specific
    ".DS_Store",
    "Thumbs.db",
    # Test directories
    "tests",
    "test",
    "**/tests",
    "**/test",
]

# Define settings for each output preset
PRESET_CONFIGS = {
    "lean": {
        "disable_ai_context": True,
        "include_repo_overview": False,
        "disable_tree": True,
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
        "disable_tree": False,
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
        "disable_tree": False,
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


def load_config(
    cli_args: Dict[str, Any], config_path_override: Optional[str] = None
) -> CodeConCatConfig:
    """
    Loads, merges, and validates the CodeConCat configuration.

    This function orchestrates the loading of configuration settings from multiple
    sources, merges them according to a defined precedence order, performs necessary
    adjustments (like path resolution and default excludes), and validates the
    final configuration using the Pydantic model.

    Configuration Sources & Precedence (lowest to highest):
    1.  Default settings defined within the `CodeConCatConfig` Pydantic model.
    2.  Preset settings selected via `output_preset` (defaults to 'medium').
        Presets (`PRESET_CONFIGS`) define common combinations of output options.
    3.  Settings loaded from a config file (`.codeconcat.yml` by default, or specified
        via `config_path_override`).
    4.  Settings explicitly provided via command-line arguments (`cli_args`).

    Special Handling:
    -   `exclude_paths`: Combines default excludes (`DEFAULT_EXCLUDE_PATTERNS`)
        with user-defined excludes from YAML/CLI.
    -   `include_paths`: Defaults to `['**/*', 'LICENSE*', 'README*']` for GitHub
        runs unless explicitly overridden by the CLI.
    -   `output`: Defaults to `code_concat_output.<format>` if not specified.
    -   `target_path`: Resolved to an absolute path.

    Args:
        cli_args: A dictionary representing the command-line arguments provided
                  by the user, typically parsed by `argparse`. Only non-default
                  values should ideally be passed to respect precedence.
        config_path_override: An optional path to a specific configuration file.
                              If provided, this path is used directly. Otherwise,
                              the function searches for '.codeconcat.yml' relative
                              to the target_path.

    Returns:
        A validated `CodeConCatConfig` object containing the merged configuration.

    Raises:
        ValidationError: If the final merged configuration fails Pydantic validation.
        FileNotFoundError: If the specified config file (`config_path_override` or
                         the default '.codeconcat.yml') does not exist or cannot be read.
        yaml.YAMLError: If the config file is malformed.
        Exception: For other unexpected errors during loading or processing.
    """
    # --- Determine Config File Path --- #
    yaml_config_raw = {}
    actual_config_path: Optional[str] = None

    if config_path_override:
        if os.path.isfile(config_path_override):
            actual_config_path = os.path.abspath(config_path_override)
            logging.info(f"Using specified config file: {actual_config_path}")
        else:
            # Raise specific error if override path doesn't exist
            raise FileNotFoundError(f"Specified config file not found: {config_path_override}")
    else:
        # Fallback to searching near target_path
        config_search_path = cli_args.get("target_path", ".")
        default_config_filename = ".codeconcat.yml"
        potential_config_path = os.path.join(config_search_path, default_config_filename)
        if os.path.isfile(potential_config_path):
            actual_config_path = os.path.abspath(potential_config_path)
            logging.info(f"Found config file: {actual_config_path}")
        else:
            logging.info("No '.codeconcat.yml' found in target directory, using defaults/CLI args.")

    # --- Load YAML Config (if path was determined) --- #
    if actual_config_path:
        try:
            with open(actual_config_path, "r", encoding="utf-8") as f:
                loaded_yaml = yaml.safe_load(f)
                if isinstance(loaded_yaml, dict):
                    yaml_config_raw = loaded_yaml
                elif loaded_yaml is not None:  # Handle empty or non-dict YAML
                    logging.warning(
                        f"Config file '{actual_config_path}' does not contain a valid dictionary."
                    )
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML config file '{actual_config_path}': {e}")
            raise  # Re-raise YAML error
        except Exception as e:
            # Catch other potential errors like permission issues
            logging.error(f"Error reading config file '{actual_config_path}': {e}")
            raise FileNotFoundError(f"Could not read config file: {actual_config_path}") from e

    # --- Determine Preset --- #
    # (Logic remains largely the same, using yaml_config_raw)
    # 1. Determine the preset (CLI > YAML > default 'medium')
    # Start by checking CLI args if 'output_preset' was provided *explicitly*
    # We need a way to distinguish between default values from argparse and user-provided ones.
    # Assuming cli_args contains only explicitly provided values or carefully filtered ones.
    # If 'output_preset' is in cli_args, it takes highest priority.
    # Otherwise, check YAML, then fall back to the Pydantic model default ('medium').

    # Temporarily load YAML just to check for 'output_preset'
    cli_preset = cli_args.get("output_preset")
    yaml_preset = yaml_config_raw.get("output_preset")

    # Validate presets found
    if cli_preset and cli_preset not in PRESET_CONFIGS:
        logging.warning(f"Invalid output_preset '{cli_preset}' from CLI. Using default.")
        cli_preset = None
    if yaml_preset and yaml_preset not in PRESET_CONFIGS:
        logging.warning(f"Invalid output_preset '{yaml_preset}' from YAML. Using default.")
        yaml_preset = None

    effective_preset_name = (
        cli_preset or yaml_preset or CodeConCatConfig().output_preset
    )  # Get model default
    logging.debug(f"Using effective output preset: '{effective_preset_name}'")

    # 2. Get base config from the chosen preset
    base_config_dict = PRESET_CONFIGS.get(effective_preset_name, PRESET_CONFIGS["medium"])

    # Create an initial config object using Pydantic defaults + preset settings
    # Start with an empty dict and update with Pydantic defaults, then preset.
    initial_config_dict = CodeConCatConfig().model_dump()  # Get all defaults from model
    initial_config_dict.update(base_config_dict)

    # 3. Layer YAML config on top (use the raw loaded YAML)
    # Only apply settings explicitly defined in the YAML file
    config_after_yaml = initial_config_dict.copy()
    for key, value in yaml_config_raw.items():
        if key in CodeConCatConfig.model_fields:  # Check if it's a valid config field
            if key != "output_preset":  # Don't overwrite the already determined preset
                config_after_yaml[key] = value
        else:
            logging.warning(f"Ignoring unknown configuration key '{key}' from .codeconcat.yml")

    # 4. Layer Explicit CLI args on top
    # Assume cli_args contains only explicitly provided values or None/defaults that should override
    config_after_cli = config_after_yaml.copy()
    for key, value in cli_args.items():
        # Only update if the CLI arg was actually provided (not None or default value, difficult to tell perfectly with argparse)
        # A common pattern is to check if the value is not None, assuming defaults are None or specific flags are used.
        # We also need to handle the 'verbose' count specifically.
        if value is not None and key in CodeConCatConfig.model_fields:
            if key == "verbose":
                # Convert integer count to boolean
                config_after_cli[key] = value > 0
            elif key == "debug" and value is True:
                # Handle deprecated --debug flag, equivalent to verbose > 1
                config_after_cli["verbose"] = True  # Set verbose to True if debug is set
            elif key == "target_path":
                # Ensure target_path is absolute before validation
                config_after_cli[key] = os.path.abspath(value) if value else os.path.abspath(".")
            elif key != "config":  # Don't store the config file path itself in the config object
                config_after_cli[key] = value
        elif key not in CodeConCatConfig.model_fields and key not in [
            "config",
            "log_level",
        ]:  # Ignore keys not in the model, except special CLI ones
            # Log ignored CLI args if needed, but might be noisy
            # logger.debug(f"Ignoring CLI argument '{key}' not in config model.")
            pass

    # --- Final Processing & Validation --- #
    final_config_dict = config_after_cli

    # Ensure target_path is absolute if not set by CLI
    if "target_path" not in final_config_dict or not final_config_dict["target_path"]:
        final_config_dict["target_path"] = os.path.abspath(".")
    elif not os.path.isabs(final_config_dict["target_path"]):
        final_config_dict["target_path"] = os.path.abspath(final_config_dict["target_path"])

    # Set default output path based on format if not provided
    if not final_config_dict.get("output"):
        output_format = final_config_dict.get(
            "format", "markdown"
        )  # Default to markdown if format missing
        final_config_dict["output"] = f"code_concat_output.{output_format}"

    # Handle default excludes
    # Combine default and user excludes carefully
    user_excludes = final_config_dict.get("exclude_paths") or []
    default_excludes = []
    # Check the boolean flag which should now be correctly set (True/False)
    if final_config_dict.get("use_default_excludes", True):
        default_excludes = DEFAULT_EXCLUDE_PATTERNS
    final_config_dict["exclude_paths"] = list(set(default_excludes + user_excludes))

    # Handle GitHub default includes (only if source_url is present and include_paths not explicitly set)
    if final_config_dict.get("source_url") and not cli_args.get("include_paths"):
        # Use GITHUB_DEFAULT_INCLUDE_PATHS if include_paths is None or empty in the final dict
        if not final_config_dict.get("include_paths"):
            final_config_dict["include_paths"] = ["**/*", "LICENSE*", "README*"]
            logging.debug("Using default include paths for GitHub source.")

    # TODO: Add more robust handling for merging list fields like include/exclude languages

    try:
        # Validate the final dictionary using the Pydantic model
        logging.debug(f"Final config dict before validation: {final_config_dict}")
        validated_config = CodeConCatConfig(**final_config_dict)
        logging.debug(f"Validated Config: {validated_config}")
        return validated_config
    except ValidationError as e:
        logging.error(f"Configuration validation failed: {e}")
        # Optionally print more details about the failed config
        # logger.error(f"Failed config data: {final_config_dict}")
        raise


# Keep apply_dict_to_config for potential future use (e.g., API)
# but it's not directly used in the new load_config flow.
def apply_dict_to_config(data: Dict[str, Any], config: CodeConCatConfig) -> None:
    """Applies settings from a dictionary to a CodeConCatConfig object.

    Iterates through the key-value pairs in the `data` dictionary and sets the
    corresponding attributes on the `config` object if they exist.

    Special Handling:
    - `custom_extension_map`: If the key is `custom_extension_map` and the value
      is a dictionary, it updates the existing dictionary on the config object
      rather than overwriting it.

    Args:
        data: A dictionary containing configuration settings to apply.
        config: The CodeConCatConfig object to update.
    """
    for key, value in data.items():
        if hasattr(config, key):
            if key == "custom_extension_map" and isinstance(value, dict):
                # Ensure the attribute exists and is a dictionary before updating
                if hasattr(config, "custom_extension_map") and isinstance(
                    config.custom_extension_map, dict
                ):
                    config.custom_extension_map.update(value)
                else:
                    # Handle cases where the attribute might not be initialized as expected
                    setattr(config, key, value)
            else:
                setattr(config, key, value)
