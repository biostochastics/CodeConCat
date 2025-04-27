import logging
import os
from typing import Any, Dict

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


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
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
    3.  Settings loaded from a `.codeconcat.yml` file found in the target directory.
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

    Returns:
        A validated `CodeConCatConfig` object containing the merged configuration.

    Raises:
        ValidationError: If the final merged configuration fails Pydantic validation.
        FileNotFoundError: If the specified `.codeconcat.yml` exists but cannot be read.
        yaml.YAMLError: If the `.codeconcat.yml` file is malformed.
        Exception: For other unexpected errors during loading or processing.
    """
    # 1. Determine the preset (CLI > YAML > default 'medium')
    # Start by checking CLI args if 'output_preset' was provided *explicitly*
    # We need a way to distinguish between default values from argparse and user-provided ones.
    # Assuming cli_args contains only explicitly provided values or carefully filtered ones.
    # If 'output_preset' is in cli_args, it takes highest priority.
    # Otherwise, check YAML, then fall back to the Pydantic model default ('medium').

    # Temporarily load YAML just to check for 'output_preset'
    yaml_config_raw = {}
    config_search_path = cli_args.get("target_path", ".")
    config_path = os.path.join(config_search_path, ".codeconcat.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_yaml = yaml.safe_load(f)
                if isinstance(loaded_yaml, dict):
                    yaml_config_raw = loaded_yaml
        except Exception as e:
            logging.warning(
                f"Could not load or parse .codeconcat.yml for preset check: {e}"
            )

    # Determine the effective preset name
    cli_preset = cli_args.get("output_preset")
    yaml_preset = yaml_config_raw.get("output_preset")

    # Validate presets found
    if cli_preset and cli_preset not in PRESET_CONFIGS:
        logging.warning(
            f"Invalid output_preset '{cli_preset}' from CLI. Using default."
        )
        cli_preset = None
    if yaml_preset and yaml_preset not in PRESET_CONFIGS:
        logging.warning(
            f"Invalid output_preset '{yaml_preset}' from YAML. Using default."
        )
        yaml_preset = None

    effective_preset_name = (
        cli_preset or yaml_preset or CodeConCatConfig().output_preset
    )  # Get model default
    logging.debug(f"Using effective output preset: '{effective_preset_name}'")

    # 2. Get base config from the chosen preset
    base_config_dict = PRESET_CONFIGS.get(
        effective_preset_name, PRESET_CONFIGS["medium"]
    )

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
            logging.warning(
                f"Ignoring unknown configuration key '{key}' from .codeconcat.yml"
            )

    # 4. Layer Explicit CLI args on top
    # Assume cli_args contains only explicitly provided args (needs careful handling in main.py)
    final_config_dict = config_after_yaml.copy()

    # Map CLI arg names to CodeConCatConfig field names if they differ
    # (Simplified mapping assuming names match for now, adjust if needed)
    cli_key_to_config_key_map = {f: f for f in CodeConCatConfig.model_fields}
    # Add specific mappings if CLI names differ from model names, e.g.:
    cli_key_to_config_key_map["github"] = "github_url"
    cli_key_to_config_key_map["ref"] = "github_ref"
    cli_key_to_config_key_map["docs"] = "extract_docs"  # Map --docs to extract_docs
    cli_key_to_config_key_map["no_tree"] = "disable_tree"
    cli_key_to_config_key_map["no_ai_context"] = "disable_ai_context"
    cli_key_to_config_key_map["no_annotations"] = "disable_annotations"
    cli_key_to_config_key_map["no_symbols"] = "disable_symbols"
    cli_key_to_config_key_map["no_copy"] = "disable_copy"
    cli_key_to_config_key_map["no_progress_bar"] = "disable_progress_bar"
    # Add mappings for the *new* fine-grained flags if their CLI names differ
    # Assuming CLI uses --include-repo-overview etc. matching the model fields

    for cli_key, value in cli_args.items():
        # Important: Only apply if the value was explicitly provided
        # This check might need refinement based on how cli_args is populated
        if value is not None:  # Basic check, might need adjustment for False flags
            config_key = cli_key_to_config_key_map.get(cli_key)
            if config_key:
                if config_key != "output_preset":  # Don't overwrite preset itself
                    # Special handling for list fields if needed (e.g., ensuring they are lists)
                    if isinstance(
                        final_config_dict.get(config_key), list
                    ) and not isinstance(value, list):
                        # Handle case where CLI provides single string for list field (if applicable)
                        final_config_dict[config_key] = [value]
                    else:
                        final_config_dict[config_key] = value
            # else: # Optional: Warn about unmapped CLI args passed to load_config
            #    logging.warning(f"CLI argument '{cli_key}' ignored (not mapped or None).")

    # 5. Handle special merging logic (exclude_paths, github includes)
    # Ensure include/exclude paths are lists, default if needed
    if not isinstance(final_config_dict.get("include_paths"), list):
        final_config_dict["include_paths"] = []
    if not isinstance(final_config_dict.get("exclude_paths"), list):
        final_config_dict["exclude_paths"] = []

    # GitHub default include logic
    is_github_run = final_config_dict.get("github_url") is not None
    cli_provided_include_paths = (
        cli_args.get("include_paths") is not None
    )  # Check if *CLI* set it

    if is_github_run and not cli_provided_include_paths:
        github_default_includes = ["**/*", "LICENSE*", "README*"]
        if final_config_dict.get("include_paths") != github_default_includes:
            final_config_dict["include_paths"] = github_default_includes
            logging.debug(
                "GitHub run detected without explicit CLI --include-paths. "
                f"Forcing include_paths to default: {github_default_includes}"
            )

    # Exclude path merging: Combine DEFAULT_EXCLUDE_PATTERNS with user paths
    user_excludes = final_config_dict.get("exclude_paths", [])
    # Ensure all user excludes are strings and filter out empty ones
    user_excludes = [str(p) for p in user_excludes if p]
    final_excludes = list(set(DEFAULT_EXCLUDE_PATTERNS + user_excludes))
    final_config_dict["exclude_paths"] = final_excludes

    # Ensure target_path is set, default to '.' if somehow missing
    if not final_config_dict.get("target_path"):
        final_config_dict["target_path"] = "."

    # 6. Validate the final merged configuration and return
    try:
        # Perform final type adjustments if needed (e.g., max_workers to int)
        if "max_workers" in final_config_dict:
            try:
                final_config_dict["max_workers"] = int(final_config_dict["max_workers"])
            except (ValueError, TypeError):
                logging.warning(
                    f"Invalid max_workers value '{final_config_dict['max_workers']}', using default 4."
                )
                final_config_dict["max_workers"] = 4  # Use a hardcoded default

        # Adjust output filename based on format if not explicitly set
        if "output" not in yaml_config_raw and "output" not in cli_args:
            final_format = final_config_dict.get("format", "markdown")
            final_config_dict["output"] = f"code_concat_output.{final_format}"

        logging.debug(
            f"Final configuration dict before validation: {final_config_dict}"
        )
        return CodeConCatConfig(**final_config_dict)

    except ValidationError as e:
        logging.error("Configuration validation failed:")
        # Provide more detailed error context
        error_details = e.errors()
        for error in error_details:
            field = ".".join(map(str, error["loc"]))
            msg = error["msg"]
            logging.error(f"  Field '{field}': {msg}")
        logging.debug(f"Failed configuration data: {final_config_dict}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred during configuration loading: {e}")
        logging.debug(f"Configuration data at time of error: {final_config_dict}")
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
