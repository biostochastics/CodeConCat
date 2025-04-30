"""Content processing module for CodeConcat."""

import os
import re
from typing import List

from ..base_types import CodeConCatConfig, ParsedFileData
from .string_utils import is_inside_string


def process_file_content(content: str, config: CodeConCatConfig) -> str:
    """Process file content according to configuration options."""
    # Don't return empty content for test files
    if not content.strip() and (
        "/tests/" in config.target_path
        or config.target_path.startswith("test_")
        or config.target_path.endswith("_test.R")
        or config.target_path.endswith("_tests.R")
    ):
        return "# Empty test file"

    # If we need to remove docstrings, do it before any other processing
    if config.remove_docstrings:
        content = remove_docstrings(content)

    lines = content.split("\n")
    processed_lines = []

    in_multiline_comment = False  # Track state for block comments /* ... */

    for i, line in enumerate(lines):
        processed_line = line

        # --- Comment Removal (only if enabled) ---
        if config.remove_comments:
            # 1. Handle Multi-line Block Comments /* ... */
            if in_multiline_comment:
                end_block_index = processed_line.find("*/")
                if end_block_index != -1:
                    # End of block comment found on this line
                    in_multiline_comment = False
                    processed_line = processed_line[end_block_index + 2 :]  # Keep content after */
                else:
                    # Line is entirely within a block comment
                    continue  # Skip this line

            # 2. Handle Start of Block Comments and Single-Line Block Comments /* ... */
            start_block_index = processed_line.find("/*")
            while start_block_index != -1:
                # Use robust string detection - ignore if inside quotes
                if not is_inside_string(processed_line, start_block_index):

                    end_block_index = processed_line.find("*/", start_block_index + 2)
                    if end_block_index != -1:
                        # Block comment starts and ends on the same line
                        # Remove the comment section
                        processed_line = (
                            processed_line[:start_block_index]
                            + processed_line[end_block_index + 2 :]
                        )
                        # Check again for more block comments on the same line
                        start_block_index = processed_line.find("/*")
                        continue  # Re-evaluate the modified line
                    else:
                        # Block comment starts but does not end on this line
                        in_multiline_comment = True
                        processed_line = processed_line[
                            :start_block_index
                        ]  # Keep content before /*
                        break  # Move to next line or process remaining part
                else:  # Inside quotes, find next potential start
                    start_block_index = processed_line.find("/*", start_block_index + 1)

            # If the line became empty after removing block comments, continue if removing empty lines
            if not processed_line.strip() and config.remove_empty_lines:
                continue
            if (
                in_multiline_comment and not processed_line.strip()
            ):  # If only /* was left and it started a block
                continue

            # 3. Handle Single-Line Comments (#, //)
            # Check only if not inside a multi-line comment that started on this line
            if not in_multiline_comment or (in_multiline_comment and processed_line.strip()):
                hash_pos = processed_line.find("#")
                slash_pos = processed_line.find("//")

                comment_pos = -1
                if hash_pos != -1 and (slash_pos == -1 or hash_pos < slash_pos):
                    # Use robust string detection
                    if not is_inside_string(processed_line, hash_pos):
                        comment_pos = hash_pos
                elif slash_pos != -1:
                    # Use robust string detection
                    if not is_inside_string(processed_line, slash_pos):
                        comment_pos = slash_pos

                if comment_pos != -1:
                    processed_line = processed_line[:comment_pos]  # Remove comment onwards
        # --- End of Comment Removal ---

        # Remove empty lines (check *after* potential comment removal)
        if config.remove_empty_lines and not processed_line.strip():
            continue

        # Add line numbers (if enabled)
        if config.show_line_numbers:
            processed_line = f"{i + 1:4d} | {processed_line}"

        processed_lines.append(processed_line)

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
    content = re.sub(r'"""[\s\S]*?"""', "", content)
    content = re.sub(r"'''[\s\S]*?'''", "", content)

    # JavaScript/TypeScript/Java JSDoc/JavaDoc style comments (/** ... */)
    # Need to be careful not to remove /* */ style comments if remove_comments is False
    content = re.sub(r"/\*\*.*?\*/", "", content, flags=re.DOTALL)

    # C# XML documentation comments (/// ...)
    content = re.sub(r"^\s*///.*$", "", content, flags=re.MULTILINE)

    # Rust documentation comments (/// ... or //! ...)
    content = re.sub(r"^\s*///.*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*//!.*$", "", content, flags=re.MULTILINE)

    # R roxygen2 comments (#' ...)
    content = re.sub(r"^\s*#'.*$", "", content, flags=re.MULTILINE)

    # Remove potential empty lines left after docstring removal
    content = re.sub(r"\n\s*\n", "\n", content)

    return content


def generate_file_summary(file_data: ParsedFileData, config: CodeConCatConfig) -> str:
    """Generate a summary for a file based on config settings."""
    summary = []
    # Basic info always included if summary is requested
    summary.append(f"- **File:** `{os.path.basename(file_data.file_path)}`")
    summary.append(f"- **Language:** `{file_data.language}`")

    # Conditionally include imports
    if config.include_imports_in_summary and file_data.imports:
        summary.append(
            f"- **Imports ({len(file_data.imports)}):** `{', '.join(sorted(file_data.imports))}`"
        )

    # Conditionally include token stats
    if config.include_tokens_in_summary and file_data.token_stats:
        summary.append("- **Token Counts:**")
        # Check for each token type individually
        if (
            hasattr(file_data.token_stats, "gpt3_tokens")
            and file_data.token_stats.gpt3_tokens is not None
        ):
            summary.append(f"  - GPT-3: `{file_data.token_stats.gpt3_tokens:,}`")
        if (
            hasattr(file_data.token_stats, "gpt4_tokens")
            and file_data.token_stats.gpt4_tokens is not None
        ):
            summary.append(f"  - GPT-4: `{file_data.token_stats.gpt4_tokens:,}`")
        if (
            hasattr(file_data.token_stats, "davinci_tokens")
            and file_data.token_stats.davinci_tokens is not None
        ):
            summary.append(f"  - DaVinci: `{file_data.token_stats.davinci_tokens:,}`")
        if (
            hasattr(file_data.token_stats, "claude_tokens")
            and file_data.token_stats.claude_tokens is not None
        ):
            summary.append(f"  - Claude: `{file_data.token_stats.claude_tokens:,}`")

    # Conditionally include security issues
    if config.include_security_in_summary and file_data.security_issues:
        summary.append("- **Security Issues:**")
        # Sort issues by severity (assuming SecurityIssue has appropriate comparison or severity enum value)
        # sorted_issues = sorted(file_data.security_issues, key=lambda issue: issue.severity, reverse=True)
        sorted_issues = file_data.security_issues  # Keep original order for now
        for issue in sorted_issues:
            # Use severity.value if it's an Enum
            severity_val = (
                issue.severity.value if hasattr(issue.severity, "value") else issue.severity
            )
            summary.append(f"  - `{severity_val}` (Line {issue.line_number}): {issue.description}")
            # Optionally include context if needed and available
            # if issue.context:
            #     summary.append(f"    Context: {issue.context}")

    # Conditionally include declarations
    if config.include_declarations_in_summary and file_data.declarations:
        summary.append("- **Declarations:**")
        # Group by kind for better readability
        decls_by_kind = {}
        for decl in file_data.declarations:
            if decl.kind not in decls_by_kind:
                decls_by_kind[decl.kind] = []
            decls_by_kind[decl.kind].append(decl.name)

        for kind, names in sorted(decls_by_kind.items()):
            summary.append(
                f"  - **{kind.capitalize()} ({len(names)}):** `{', '.join(sorted(names))}`"
            )
            # Optionally list individual declarations if verbose
            # for decl in sorted(file_data.declarations, key=lambda d: d.start_line):
            #     summary.append(
            #         f"  - {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})"
            #     )

    # Return empty string if no summary parts were added beyond basic info and flags disable them
    if len(summary) == 2:
        return ""  # Or perhaps a default message like "No summary details enabled."

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
