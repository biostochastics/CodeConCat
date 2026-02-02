"""AI context generation for CodeConcat output."""

import logging
import os

from codeconcat.base_types import AnnotatedFileData, ParsedDocData, WritableItem

logger = logging.getLogger(__name__)


def generate_ai_preamble(
    items: list[WritableItem],
) -> str:
    """Generate an AI-friendly preamble that explains the codebase structure and contents.

    Analyzes the provided items to generate statistics, identify entry points,
    and create a summary suitable for AI code analysis and understanding.

    Args:
        items: List of WritableItem objects (AnnotatedFileData or ParsedDocData)
               containing parsed code and documentation files.

    Returns:
        str: A markdown-formatted preamble containing codebase statistics,
             structure overview, and key files summary.
    """

    # --- Filter items into specific types --- #
    code_files: list[AnnotatedFileData] = []
    doc_files: list[ParsedDocData] = []
    for item in items:
        if isinstance(item, AnnotatedFileData):
            code_files.append(item)
        elif isinstance(item, ParsedDocData):
            doc_files.append(item)
        # Note: If other WritableItem types exist, they are ignored here.

    # --- Calculate Stats (mostly from code files) --- #
    file_types: dict[str, int] = {}
    total_functions = 0
    total_function_lines = 0
    for file in code_files:
        try:
            # Safely extract file extension
            ext = file.file_path.split(".")[-1] if "." in file.file_path else "unknown"
            file_types[ext] = file_types.get(ext, 0) + 1

            # Handle missing or None declarations attribute
            declarations = getattr(file, "declarations", [])
            if declarations:
                for element in declarations:
                    try:
                        if getattr(element, "kind", None) == "function":
                            total_functions += 1
                            start_line = getattr(element, "start_line", 0)
                            end_line = getattr(element, "end_line", 0)
                            if start_line and end_line:
                                total_function_lines += end_line - start_line + 1
                    except (AttributeError, TypeError) as e:
                        logger.debug(f"Error processing declaration in {file.file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error processing file {getattr(file, 'file_path', 'unknown')}: {e}")

    avg_function_length = (
        round(total_function_lines / total_functions, 1) if total_functions > 0 else 0
    )

    # Identify potential entry points
    common_entry_points = [
        "main.py",
        "__main__.py",
        "app.py",
        "server.py",
        "manage.py",
        "index.js",
        "server.js",
        "app.js",
        "index.ts",
        "server.ts",
        "app.ts",
        # Add more common entry points as needed
    ]
    potential_entry_files = [
        file.file_path
        for file in code_files
        if os.path.basename(file.file_path) in common_entry_points
    ]

    # Identify key files (based on having annotations/summaries)
    key_files_with_summaries = []
    for file in code_files:
        try:
            # Safely access summary attribute with default
            summary = getattr(file, "summary", None)
            if summary:
                file_path = getattr(file, "file_path", "unknown")
                key_files_with_summaries.append(f"- `{file_path}`: {summary}")
        except Exception as e:
            logger.debug(f"Error accessing summary for file: {e}")

    # Generate summary
    lines = [
        "# AI-Friendly Code Summary",
        "",
        "This document contains a structured representation of a codebase, organized for AI analysis.",
        "",
        "## Repository Structure",
        "```",
        f"Total code files: {len(code_files)}",
        f"Documentation files: {len(doc_files)}",
        f"Total functions found: {total_functions}",
        f"Average function length: {avg_function_length} lines",
        "",
        "File types:",
    ]

    for ext, count in sorted(file_types.items()):
        lines.append(f"- {ext}: {count} files")

    lines.extend(
        [
            "```",
            "",
            "## Potential Entry Points",
        ]
    )
    if potential_entry_files:
        lines.append("The following files might be primary entry points:")
        lines.extend([f"- `{f}`" for f in potential_entry_files])
    else:
        lines.append("No common entry point files detected.")

    lines.extend(
        [
            "",
            "## Key Files",
            "Key files based on available annotations:",
        ]
    )
    if key_files_with_summaries:
        lines.extend(key_files_with_summaries)
    else:
        lines.append("No files with summary annotations found.")

    lines.extend(
        [
            "",
            "## Code Organization",
            "The code is organized into sections, each prefixed with clear markers:",
            "- Directory markers show file organization",
            "- File headers contain metadata and imports",
            "- Annotations provide context about code purpose",
            "- Documentation sections contain project documentation",
            "",
            "## Navigation",
            "- Each file begins with '---FILE:' followed by its path",
            "- Each section is clearly delimited with markdown headers",
            "- Code blocks are formatted with appropriate language tags",
            "",
        ]
    )

    lines.extend(["", "---", "Begin code content below:", ""])

    return "\n".join(lines)
