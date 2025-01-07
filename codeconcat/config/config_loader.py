import os
import yaml
import logging
from typing import Dict, Any
from codeconcat.types import CodeConCatConfig


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
    """
    Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
    CLI args take precedence over the config file.
    """
    config_data = {}

    # Try to load .codeconcat.yml if it exists
    target_path = cli_args.get("target_path", ".")
    config_path = os.path.join(target_path, ".codeconcat.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[CodeConCat] Warning: Failed to load .codeconcat.yml: {e}")

    # CLI-only arguments that shouldn't be passed to config
    cli_only_args = {"init", "debug"}

    # Filter out CLI-only arguments
    filtered_args = {k: v for k, v in cli_args.items() if k not in cli_only_args}

    # Merge CLI args with config file (CLI takes precedence)
    merged = {**config_data, **filtered_args}

    # Map CLI arg names to config field names
    field_mapping = {
        "include": "include_paths",
        "exclude": "exclude_paths",
        "docs": "extract_docs",
        "no_tree": "disable_tree",
        "no_copy": "disable_copy",
        "no_annotations": "disable_annotations",
        "no_symbols": "disable_symbols",
        "github": "github_url",
        "ref": "github_ref"
    }

    # Rename fields to match CodeConCatConfig
    for cli_name, config_name in field_mapping.items():
        if cli_name in merged:
            merged[config_name] = merged.pop(cli_name)

    # Ensure target_path is set
    merged["target_path"] = target_path

    logging.debug("Merged config data before creating config: %s", merged)

    # Create config object
    try:
        return CodeConCatConfig(**merged)
    except TypeError as e:
        logging.error("Failed to create config: %s", e)
        logging.error("Available fields in CodeConCatConfig: %s", CodeConCatConfig.__dataclass_fields__.keys())
        logging.error("Attempted fields: %s", merged.keys())
        raise


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
