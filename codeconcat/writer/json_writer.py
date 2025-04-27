import json
from typing import List

from codeconcat.base_types import (
    CodeConCatConfig,
    WritableItem,
)


def write_json(
    items: List[WritableItem],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Generate JSON output, conditionally including fields based on config."""
    output_data = {}

    # --- Top Level: Repository Overview --- #
    # Includes folder tree
    if (
        config.include_repo_overview
        and config.include_directory_structure
        and folder_tree_str
    ):
        output_data["repository_overview"] = {"directory_structure": folder_tree_str}

    # --- Files Section --- #
    # Always include the 'files' list, but its contents depend on flags
    output_data["files"] = []

    # Combine and sort items if requested
    items_to_process = items
    if config.sort_files:
        items_to_process.sort(key=lambda x: x.file_path)

    # Single loop processing all items polymorphically
    for item in items_to_process:
        item_dict = item.render_json_dict(config)
        # Only append if the render method returned something (it should always return dict)
        if item_dict:
            output_data["files"].append(item_dict)

    # Generate final JSON string
    # Use model_dump_json for Pydantic objects if applicable, else default encoder
    final_json = json.dumps(
        output_data, indent=config.json_indent, default=str
    )  # Use default=str for non-serializable

    # Writing to file is handled by the caller (e.g., cli_entry_point)
    # logger = logging.getLogger(__name__)
    # logger.info(f"JSON data generated (will be written to: {config.output})")

    return final_json
