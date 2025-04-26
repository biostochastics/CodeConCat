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


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
    """
    Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
    Priority order: CLI args > .codeconcat.yml > Defaults.
    """
    # Define defaults *excluding* exclude_paths, which needs special handling
    base_defaults = {
        "target_path": ".",
        "github_url": None,
        "github_token": None,
        "github_ref": None,
        "include_languages": [],
        "exclude_languages": [],
        "include_paths": ["**/*", "LICENSE*", "README*"],
        # "exclude_paths": [], # Handled separately below
        "extract_docs": False,
        "merge_docs": False,
        "output": "code_concat_output.md",
        "format": "markdown",
        "max_workers": 4,
        "include_file_summary": True,
        "include_directory_structure": True,
        "remove_comments": True,
        "remove_docstrings": True,
        "remove_empty_lines": True,
        "show_line_numbers": True,
        "enable_docs": False,
        "enable_ai_context": True,
        "enable_annotations": True,
        "disable_symbols": False,
    }

    # 2. Try to load .codeconcat.yml if it exists
    yaml_config = {}
    # Use target_path from CLI if provided, else default '.' for finding config
    config_search_path = cli_args.get("target_path", ".")
    config_path = os.path.join(config_search_path, ".codeconcat.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_yaml = yaml.safe_load(f)
                if isinstance(loaded_yaml, dict):
                    yaml_config = loaded_yaml
                else:
                    logging.warning(
                        f".codeconcat.yml at {config_path} is not a valid dictionary, ignoring."
                    )
        except yaml.YAMLError as e:
            logging.error(f"Error parsing .codeconcat.yml: {e}")
        except Exception as e:
            logging.error(f"Failed to load .codeconcat.yml: {e}")

    # 3. Prepare CLI args, mapping names and filtering Nones where appropriate
    # Keep only args that were actually provided via CLI AND are not None
    # (unless None is a valid value for that specific key)
    cli_key_to_config_key_map = {
        "target_path": "target_path",
        "github": "github_url",
        "github_token": "github_token",
        "ref": "github_ref",
        "include_languages": "include_languages",
        "exclude_languages": "exclude_languages",
        "include_paths": "include_paths",
        "exclude_paths": "exclude_paths",
        "docs": "enable_docs",  # Note: maps to enable_docs
        "merge_docs": "merge_docs",
        "output": "output",
        "format": "format",
        "max_workers": "max_workers",
        "include_file_summary": "include_file_summary",
        "include_directory_structure": "include_directory_structure",
        "remove_comments": "remove_comments",
        "remove_docstrings": "remove_docstrings",
        "remove_empty_lines": "remove_empty_lines",
        "show_line_numbers": "show_line_numbers",
        "enable_ai_context": "enable_ai_context",
        "enable_annotations": "enable_annotations",
        "disable_symbols": "disable_symbols",
        # Map legacy/deprecated flags if necessary
    }

    # Handle flags that disable features (e.g., --no-tree)
    # These often correspond to setting a config key like 'disable_tree' to True
    # Assuming cli_args contains keys like 'no_tree', 'no_copy', etc.
    # We need to map them to the correct config key (e.g., 'disable_tree')
    # and set the value to True if the flag was present.
    # This mapping depends heavily on how argparse is configured.
    # For now, we assume the boolean flags are directly in cli_args with correct polarity.

    config_from_cli = {}
    for cli_key, value in cli_args.items():
        # Only consider args explicitly passed (value is not None)
        # or args where None is explicitly allowed (e.g., potentially github_token)
        if value is not None or cli_key in ["github_token"]:  # Add keys where None is allowed
            if cli_key in cli_key_to_config_key_map:
                config_key = cli_key_to_config_key_map[cli_key]
                # Special handling for exclude_paths filtering
                if config_key == "exclude_paths" and isinstance(value, list):
                    config_from_cli[config_key] = [x for x in value if x]
                else:
                    config_from_cli[config_key] = value
            # else: # Optional: Warn about unmapped CLI args
            #     logging.warning(f"Unrecognized CLI argument ignored: {cli_key}")

    # 4. Merge configurations: Defaults < YAML < Explicit CLI
    merged = {**base_defaults, **yaml_config, **config_from_cli}

    # Special handling for GitHub runs: If --github is used and --include-paths is NOT explicitly
    # provided via CLI, default to including everything ('**/*') plus LICENSE/README,
    # overriding any potentially restrictive 'include_paths' from the YAML config.
    is_github_run = merged.get("github_url") is not None
    cli_provided_include_paths = cli_args.get("include_paths") is not None

    if is_github_run and not cli_provided_include_paths:
        # Force the desired default for GitHub runs when not explicitly overridden by CLI
        github_default_includes = ['**/*', 'LICENSE*', 'README*']
        if merged.get("include_paths") != github_default_includes:
            merged["include_paths"] = github_default_includes
            logging.debug(
                "GitHub run detected without explicit CLI --include-paths. "
                f"Forcing include_paths to default: {github_default_includes}"
            )

    # 5. Special handling for exclude_paths: Combine defaults with user-provided
    user_excludes = merged.get("exclude_paths", [])
    if not isinstance(user_excludes, list):
        logging.warning(
            f"Invalid 'exclude_paths' format in config: {user_excludes}. Using defaults only."
        )
        user_excludes = []
    else:
        # Ensure all user excludes are strings
        user_excludes = [str(p) for p in user_excludes if p]

    # Combine defaults and user excludes, remove duplicates
    final_excludes = list(set(DEFAULT_EXCLUDE_PATTERNS + user_excludes))
    merged["exclude_paths"] = final_excludes

    # 5. Validate the final merged configuration
    try:
        # This check is now done during the merge logic above, but keep basic list check
        if "exclude_paths" not in merged or not isinstance(merged["exclude_paths"], list):
            logging.error("Internal Error: exclude_paths is not a list after merging.")
            merged["exclude_paths"] = DEFAULT_EXCLUDE_PATTERNS  # Fallback

        # Perform final type checks or adjustments if needed before validation
        # e.g., ensure max_workers is an int
        if "max_workers" in merged:
            try:
                merged["max_workers"] = int(merged["max_workers"])
            except (ValueError, TypeError):
                logging.warning(
                    f"Invalid max_workers value '{merged['max_workers']}', using default {base_defaults['max_workers']}."
                )
                merged["max_workers"] = base_defaults["max_workers"]

        return CodeConCatConfig(**merged)
    except ValidationError as e:
        logging.error("Configuration validation failed:")
        logging.error(str(e))
        # Log the final merged dictionary that failed validation for debugging
        logging.debug(f"Failed configuration data: {merged}")
        raise


def apply_dict_to_config(data: Dict[str, Any], config: CodeConCatConfig) -> None:
    for key, value in data.items():
        if hasattr(config, key):
            if key == "custom_extension_map" and isinstance(value, dict):
                config.custom_extension_map.update(value)
            else:
                setattr(config, key, value)
