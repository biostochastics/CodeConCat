import os
import yaml
from typing import Dict, Any
from codeconcat.types import CodeConCatConfig


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
    """
    Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
    CLI args take precedence over the config file.
    """
    config_data = {}

    # Try to load .codeconcat.yml if it exists
    config_path = os.path.join(cli_args.get("target_path", "."), ".codeconcat.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[CodeConCat] Warning: Failed to load .codeconcat.yml: {e}")

    # Merge CLI args with config file (CLI takes precedence)
    merged = {**config_data, **cli_args}

    # Always set merge_docs to False to ensure docs are output separately
    merged["merge_docs"] = False

    return CodeConCatConfig(**merged)


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
