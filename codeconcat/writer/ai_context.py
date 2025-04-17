"""AI context generation for CodeConcat output."""

import os
from typing import Dict, List

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeElementType,
    ParsedDocData,
    ParsedFileData,
)


def generate_ai_preamble(
    code_files: List[ParsedFileData],
    doc_files: List[ParsedDocData],
    file_annotations: Dict[str, AnnotatedFileData],
) -> str:
    """Generate an AI-friendly preamble that explains the codebase structure and contents."""

    # Count files by type and calculate complexity metrics
    file_types = {}
    total_functions = 0
    total_function_lines = 0
    for file in code_files:
        ext = file.file_path.split(".")[-1] if "." in file.file_path else "unknown"
        file_types[ext] = file_types.get(ext, 0) + 1

        for element in file.elements:
            if element.type == CodeElementType.FUNCTION:
                total_functions += 1
                total_function_lines += (element.end_line - element.start_line + 1)

    avg_function_length = (
        round(total_function_lines / total_functions, 1)
        if total_functions > 0
        else 0
    )

    # Identify potential entry points
    common_entry_points = [
        "main.py", "__main__.py", "app.py", "server.py", "manage.py",
        "index.js", "server.js", "app.js",
        "index.ts", "server.ts", "app.ts",
        # Add more common entry points as needed
    ]
    potential_entry_files = [
        file.file_path
        for file in code_files
        if os.path.basename(file.file_path) in common_entry_points
    ]

    # Identify key files (based on having annotations)
    key_files_with_summaries = []
    for file in code_files:
        annotation = file_annotations.get(
            file.file_path, AnnotatedFileData(file.file_path, "", [])
        )
        if annotation.summary:
            key_files_with_summaries.append(f"- `{file.file_path}`: {annotation.summary}")

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
