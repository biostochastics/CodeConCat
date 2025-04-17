import logging
import os
from typing import Any, Dict

import yaml
from pydantic import ValidationError

from codeconcat.base_types import CodeConCatConfig


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
    """
    Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
    CLI args take precedence over the config file.
    """
    # Convert CLI args to config format
    config_dict = {
        "target_path": cli_args.get("target_path", "."),
        "github_url": cli_args.get("github"),
        "github_token": cli_args.get("github_token"),
        "github_ref": cli_args.get("ref"),
        "include_languages": cli_args.get("include_languages", []),
        "exclude_languages": cli_args.get("exclude_languages", []),
        "include_paths": cli_args.get("include", []),
        "exclude_paths": [x for x in cli_args.get("exclude", []) if x],  # Filter out empty strings
        "extract_docs": cli_args.get("docs", False),
        "merge_docs": cli_args.get("merge_docs", False),
        "output": cli_args.get("output", "code_concat_output.md"),
        "format": cli_args.get("format", "markdown"),
        "max_workers": cli_args.get("max_workers", 2),
        "disable_tree": cli_args.get("no_tree", False),
        "disable_copy": cli_args.get("no_copy", False),
        "disable_annotations": cli_args.get("no_annotations", False),
        "disable_symbols": cli_args.get("no_symbols", False),
        "disable_ai_context": cli_args.get("no_ai_context", False),
    }

    # Try to load .codeconcat.yml if it exists
    yaml_config = {}
    target_path = cli_args.get("target_path", ".")
    config_path = os.path.join(target_path, ".codeconcat.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Failed to load .codeconcat.yml: {e}")
            yaml_config = {}

    # Merge configs, CLI args take precedence
    merged = {**yaml_config, **config_dict}

    try:
        return CodeConCatConfig(**merged)
    except ValidationError as e:
        # Provide more detailed Pydantic error messages
        logging.error(f"Configuration validation failed:")
        # Use e.errors() for structured details or str(e) for a formatted summary
        logging.error(str(e))  # Log the formatted error message from Pydantic
        # Optionally log raw data for debugging:
        # logging.error(f"Attempted configuration data: {merged}")
        raise  # Re-raise the exception


def read_config_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def apply_dict_to_config(data: Dict[str, Any], config: CodeConCatConfig) -> None:
    for key, value in data.items():
        if hasattr(config, key):
            if key == "custom_extension_map" and isinstance(value, dict):
                config.custom_extension_map.update(value)
            else:
                setattr(config, key, value)
