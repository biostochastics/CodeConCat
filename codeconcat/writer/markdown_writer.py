from __future__ import annotations

import logging
import os
import random
import re
from typing import List

import tiktoken
from halo import Halo

from codeconcat.base_types import (
    PROGRAMMING_QUOTES,
    CodeConCatConfig,
    Declaration,
    WritableItem,
)
from .ai_context import generate_ai_preamble

logger = logging.getLogger(__name__)


def count_tokens(text: str) -> int:
    """Count tokens using GPT-4 tokenizer (cl100k_base)."""
    try:
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))
    except Exception as e:
        logger.info(
            f"Warning: Tiktoken encoding failed ({str(e)}), falling back to word count"
        )
        return len(text.split())


def print_quote_with_ascii(total_output_tokens: int = None):
    """Print a random programming quote with ASCII art frame."""
    quote = random.choice(PROGRAMMING_QUOTES)
    quote_tokens = count_tokens(quote)

    # Calculate width for the ASCII art frame
    width = max(len(line) for line in quote.split("\n")) + 4

    # ASCII art frame
    top_border = "+" + "=" * (width - 2) + "+"
    empty_line = "|" + " " * (width - 2) + "|"

    # Build the complete output string
    output_lines = ["\n[CodeConCat] Meow:", top_border, empty_line]

    # Word wrap the quote to fit in the frame
    words = quote.split()
    current_line = "|  "
    for word in words:
        if len(current_line) + len(word) + 1 > width - 2:
            output_lines.append(
                current_line + " " * (width - len(current_line) - 1) + "|"
            )
            current_line = "|  " + word
        else:
            if current_line == "|  ":
                current_line += word
            else:
                current_line += " " + word
    output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")

    output_lines.extend([empty_line, top_border])

    # Print everything
    logger.info("\n".join(output_lines))
    logger.info(f"\nQuote tokens (GPT-4): {quote_tokens:,}")
    if total_output_tokens:
        logger.info(f"Total CodeConcat output tokens (GPT-4): {total_output_tokens:,}")


def is_test_or_config_file(file_path: str) -> bool:
    """Check if a file is a test or configuration file."""
    file_name = os.path.basename(file_path).lower()
    return (
        file_name.startswith("test_")
        or file_name == "setup.py"
        or file_name == "conftest.py"
        or file_name.endswith("config.py")
        or "tests/" in file_path
    )


def _generate_anchor_name(file_path: str, decl: Declaration) -> str:
    """Generate a sanitized, unique anchor name for a declaration."""
    # Normalize file path: remove leading './', replace slashes and dots
    norm_path = file_path.lstrip("./").replace("/", "_").replace(".", "_")
    # Sanitize declaration name: keep alphanumeric, hyphen, underscore
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "", decl.name)
    # Combine parts
    anchor = f"symbol-{norm_path}-{decl.kind}-{safe_name}".lower()
    return anchor


def write_markdown(
    items: List[WritableItem],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Write the concatenated code and docs to a markdown file, respecting config flags."""
    spinner = Halo(text="Generating Markdown output", spinner="dots")
    spinner.start()

    output_parts = []
    output_parts.append("# CodeConCat Output\n\n")

    # --- Section: Repository Overview --- #
    # This includes AI preamble and potentially the folder tree
    if config.include_repo_overview:
        spinner.text = "Generating repository overview"
        # Generate AI preamble (if not disabled implicitly by preset/flag)
        # We might need a more specific flag like 'include_ai_preamble' later
        # For now, tie it to repo overview
        if not config.disable_ai_context:
            # Pass items list only, as config is no longer needed by generate_ai_preamble
            ai_preamble = generate_ai_preamble(items)
            if ai_preamble:
                output_parts.append(ai_preamble)
                output_parts.append("\n")

        # Add directory structure if configured and provided
        if config.include_directory_structure and folder_tree_str:
            spinner.text = "Adding directory structure"
            output_parts.append("## Directory Structure\n")
            output_parts.append(f"```\n{folder_tree_str}\n```\n\n")
        output_parts.append("---\n\n")

    # --- File Index --- #
    if config.include_file_index:
        output_parts.append("## File Index")
        output_parts.append("```")
        # Sort items if needed for index consistency with file section
        items_for_index = (
            sorted(items, key=lambda x: x.file_path) if config.sort_files else items
        )
        for item in items_for_index:
            output_parts.append(item.file_path)
        output_parts.append("```")
        output_parts.append("\n")

    # --- Files Section (Unified) --- #
    output_parts.append("## Files")
    output_parts.append("\n")

    # Sort items if requested before processing
    items_to_process = (
        sorted(items, key=lambda x: x.file_path) if config.sort_files else items
    )

    # Single loop processing all items polymorphically
    if not items_to_process:
        output_parts.append("_No files or documents found._")
    else:
        for item in items_to_process:
            # Polymorphic call to render markdown chunks
            md_chunks = item.render_markdown_chunks(config)
            output_parts.extend(md_chunks)
            output_parts.append("\n---\n")  # Separator between files

    spinner.text = "Finalizing output"
    final_str = "\n".join(output_parts)

    # Count tokens for the entire output
    spinner.text = "Counting tokens"
    output_tokens = count_tokens(final_str)

    # Add token count information at the end of the string
    final_str += "\n\n<!-- Token Count -->\n"
    final_str += (
        f"<!-- Total CodeConCat output tokens (cl100k_base): {output_tokens:,} -->\n"
    )

    spinner.succeed("Markdown generation complete")
    # Logging is handled by the caller (e.g., run_codeconcat)

    # Print quote with ASCII art, passing the total output tokens
    print_quote_with_ascii(output_tokens)

    return final_str
