import os
import yaml
from typing import Dict, Any
from codeconcat.types import CodeConCatConfig


def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
    config = CodeConCatConfig()
    file_data = read_config_file(".codeconcat.yml")

    if file_data:
        apply_dict_to_config(file_data, config)

    apply_dict_to_config(cli_args, config)

    return config


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
