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
    if config.include_repo_overview and config.include_directory_structure and folder_tree_str:
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
            # Add compression segments if available
            if (
                config.enable_compression
                and hasattr(config, "_compressed_segments")
                and hasattr(item, "file_path")
            ):
                # Find segments related to this file
                file_segments = [
                    s for s in config._compressed_segments if hasattr(item, "file_path")
                ]
                if file_segments:
                    # Add segments to the item
                    item_dict["content_segments"] = [
                        {
                            "type": segment.segment_type.value,
                            "start_line": segment.start_line,
                            "end_line": segment.end_line,
                            "content": segment.content,
                            "metadata": segment.metadata,
                        }
                        for segment in file_segments
                    ]
            output_data["files"].append(item_dict)

    # Generate final JSON string
    # Use model_dump_json for Pydantic objects if applicable, else default encoder
    # Get indent parameter with a default of 2 if not defined in config
    indent = getattr(config, "json_indent", 2)
    final_json = json.dumps(
        output_data, indent=indent, default=str
    )  # Use default=str for non-serializable

    # Writing to file is handled by the caller (e.g., cli_entry_point)
    # logger = logging.getLogger(__name__)
    # logger.info(f"JSON data generated (will be written to: {config.output})")

    return final_json
