"""AI context generation for CodeConcat output."""

from typing import List, Dict
from codeconcat.base_types import ParsedFileData, ParsedDocData, AnnotatedFileData

def generate_ai_preamble(
    code_files: List[ParsedFileData],
    doc_files: List[ParsedDocData],
    file_annotations: Dict[str, AnnotatedFileData]
) -> str:
    """Generate an AI-friendly preamble that explains the codebase structure and contents."""
    
    # Count files by type
    file_types = {}
    for file in code_files:
        ext = file.file_path.split('.')[-1] if '.' in file.file_path else 'unknown'
        file_types[ext] = file_types.get(ext, 0) + 1

    # Generate summary
    lines = [
        "# CodeConcat AI-Friendly Code Summary",
        "",
        "This document contains a structured representation of a codebase, organized for AI analysis.",
        "",
        "## Repository Structure",
        "```",
        f"Total code files: {len(code_files)}",
        f"Documentation files: {len(doc_files)}",
        "",
        "File types:",
    ]
    
    for ext, count in sorted(file_types.items()):
        lines.append(f"- {ext}: {count} files")
    
    lines.extend([
        "```",
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
        "## Content Summary",
    ])

    # Add file listing
    for file in code_files:
        annotation = file_annotations.get(file.file_path, AnnotatedFileData(file.file_path, "", []))
        if annotation.summary:
            lines.append(f"- `{file.file_path}`: {annotation.summary}")

    lines.extend([
        "",
        "---",
        "Begin code content below:",
        ""
    ])

    return "\n".join(lines)
