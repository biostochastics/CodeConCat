"""Content processing module for CodeConcat."""

import os
import re
from typing import List, Optional

from ..base_types import AnnotatedFileData, CodeConCatConfig, Declaration, ParsedFileData
from .security_processor import SecurityProcessor
from .token_counter import count_tokens


def process_file_content(content: str, config: CodeConCatConfig) -> str:
    """Process file content according to configuration options."""
    # Don't return empty content for test files
    if not content.strip() and (
        "/tests/" in config.target_path or 
        config.target_path.startswith("test_") or 
        config.target_path.endswith("_test.R") or
        config.target_path.endswith("_tests.R")
    ):
        return "# Empty test file"
    
    # If we need to remove docstrings, do it before any other processing
    if config.remove_docstrings:
        content = remove_docstrings(content)
        
    lines = content.split("\n")
    processed_lines = []

    for i, line in enumerate(lines):
        # Skip if it's an empty line and we're removing empty lines
        if config.remove_empty_lines and not line.strip():
            continue

        # Skip if it's a comment and we're removing comments
        if config.remove_comments:
            stripped = line.strip()
            if (
                stripped.startswith("#")
                or stripped.startswith("//")
                or stripped.startswith("/*")
                or stripped.startswith("*")
                or stripped.startswith('"""')
                or stripped.startswith("'''")
                or stripped.endswith("*/")
            ):
                continue

        # Add line number if configured
        if config.show_line_numbers:
            line = f"{i+1:4d} | {line}"

        processed_lines.append(line)

    return "\n".join(processed_lines)


def remove_docstrings(content: str) -> str:
    """Remove documentation strings from code.
 
    It preserves inline comments (#, //).
 
    Args:
        content: The source code content
        
    Returns:
        Code content with docstrings removed
    """
    # Python triple-quoted docstrings (both ''' and """)
    # Using non-greedy matching and handling escaped quotes within docstrings requires
    # more complex regex or a proper parser. This simpler version works for most cases.
    content = re.sub(r'"""[\s\S]*?"""', '', content)
    content = re.sub(r"'''[\s\S]*?'''", '', content)

    # JavaScript/TypeScript/Java JSDoc/JavaDoc style comments (/** ... */)
    # Need to be careful not to remove /* */ style comments if remove_comments is False
    content = re.sub(r'/\*\*.*?\*/', '', content, flags=re.DOTALL)

    # C# XML documentation comments (/// ...)
    content = re.sub(r'^\s*///.*$', '', content, flags=re.MULTILINE)

    # Rust documentation comments (/// ... or //! ...)
    content = re.sub(r'^\s*///.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*//!.*$', '', content, flags=re.MULTILINE)

    # R roxygen2 comments (#' ...)
    content = re.sub(r"^\s*#'.*$", '', content, flags=re.MULTILINE)
    
    # Remove potential empty lines left after docstring removal
    content = re.sub(r'\n\s*\n', '\n', content)

    return content


def generate_file_summary(file_data: ParsedFileData) -> str:
    """Generate a summary for a file."""
    summary = []
    summary.append(f"File: {os.path.basename(file_data.file_path)}")
    summary.append(f"Language: {file_data.language}")

    if file_data.token_stats:
        summary.append("Token Counts:")
        summary.append(f"  - Input: {file_data.token_stats.input_tokens:,}")
        summary.append(f"  - Output: {file_data.token_stats.output_tokens:,}")
        summary.append(f"  - Total: {file_data.token_stats.total_tokens:,}")

    if file_data.security_issues:
        summary.append("\nSecurity Issues:")
        for issue in file_data.security_issues:
            summary.append(f"  - {issue.rule_id} ({issue.severity.name}, Line {issue.line_number})")
            summary.append(f"    Context: {issue.context}")

    if file_data.declarations:
        summary.append("\nDeclarations:")
        for decl in file_data.declarations:
            summary.append(
                f"  - {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})"
            )

    return "\n".join(summary)


def generate_directory_structure(file_paths: List[str]) -> str:
    """Generate a tree-like directory structure."""
    structure = {}
    for path in file_paths:
        parts = path.split(os.sep)
        current = structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = None

    def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> List[str]:
        lines = []
        if node is None:
            return lines

        items = list(node.items())
        for i, (name, subtree) in enumerate(items):
            is_last_item = i == len(items) - 1
            lines.append(f"{prefix}{'└── ' if is_last_item else '├── '}{name}")
            if subtree is not None:
                extension = "    " if is_last_item else "│   "
                lines.extend(print_tree(subtree, prefix + extension, is_last_item))
        return lines

    return "\n".join(print_tree(structure))
