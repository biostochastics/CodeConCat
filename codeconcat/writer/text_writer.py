"""Plain text writer for CodeConcat output."""

# Use forward reference for type hint
from __future__ import annotations

import logging
from typing import List

from codeconcat.base_types import (
    CodeConCatConfig,
    WritableItem,
)

logger = logging.getLogger(__name__)

SEPARATOR_LENGTH = 80  # Define the constant


def write_text(
    items: List[WritableItem],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to a plain text string, respecting config flags."""
    output_lines = []

    # --- Repository Overview --- #
    if config.include_repo_overview:
        output_lines.append("#" * SEPARATOR_LENGTH)
        output_lines.append("# Repository Overview")
        output_lines.append("#" * SEPARATOR_LENGTH)
        if config.include_directory_structure and folder_tree_str:
            output_lines.append("\n## Directory Structure:")
            output_lines.append(folder_tree_str)
        output_lines.append("\n")

    # --- File Index --- #
    if config.include_file_index:
        output_lines.append("#" * SEPARATOR_LENGTH)
        output_lines.append("# File Index")
        output_lines.append("#" * SEPARATOR_LENGTH)
        # Assumes items list is already sorted if config.sort_files is True
        # If not sorted here, the index might not match sorted file output section.
        # Caller (main.py/cli_entry_point.py) should handle sorting before passing 'items'.
        for i, item in enumerate(items):
            output_lines.append(f"{i + 1}. {item.file_path}")
        output_lines.append("\n")

    # --- Files Section --- #
    output_lines.append("#" * SEPARATOR_LENGTH)
    output_lines.append("# File Content")
    output_lines.append("#" * SEPARATOR_LENGTH)
    output_lines.append("\n")

    items_to_process = (
        sorted(items, key=lambda x: x.file_path) if config.sort_files else items
    )

    if not items_to_process:
        output_lines.append("_No files or documents found._")
    else:
        for i, item in enumerate(items_to_process):
            output_lines.append("-" * SEPARATOR_LENGTH)
            output_lines.append(f"File: {item.file_path}")
            output_lines.append("-" * SEPARATOR_LENGTH)

            # Polymorphic call to render text lines
            item_lines = item.render_text_lines(config)
            output_lines.extend(item_lines)

            output_lines.append("\n")  # Add a newline after each file section

    output_string = "\n".join(output_lines)
    logger.info(
        f"Generated text output for {len(items)} files "
        f"with total length {len(output_string)} characters"
    )
    return output_string
