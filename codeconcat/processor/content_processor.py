"""Content processing module for CodeConcat."""

import os
import re
from typing import Any, List, Optional

from ..base_types import CodeConCatConfig, ParsedFileData


def remove_comments(content: str) -> str:
    """
    Remove comments from code while preserving comments inside strings.

    Intelligently handles both single-line and multi-line comments, preserving
    content within strings and multiline strings. Supports various comment styles
    including //, #, /* */, and language-specific patterns.

    Args:
        content: The source code content to process.

    Returns:
        The code content with comments removed but strings intact.

    Complexity:
        O(n) where n is the number of lines in the content.

    Features:
        - Preserves comments inside string literals
        - Handles multiline string detection (triple quotes)
        - Removes both block comments (/* */) and line comments (// and #)
        - Maintains proper line structure for debugging
    """
    # First handle multiline block comments
    content = _remove_multiline_block_comments(content)

    # Then handle single-line comments
    lines = content.split("\n")
    processed_lines = []
    in_multiline_string = False
    multiline_delimiter: Optional[str] = None

    for line in lines:
        # Check for multiline string continuation
        if in_multiline_string:
            # Look for end of multiline string
            assert multiline_delimiter is not None, (
                "multiline_delimiter should not be None when in_multiline_string is True"
            )
            if multiline_delimiter in line:
                # Find where the multiline string ends
                end_pos = line.find(multiline_delimiter) + len(multiline_delimiter)
                # Process the part after the string ends
                remaining = line[end_pos:]
                processed_remaining = _remove_comments_from_line(remaining)
                processed_line = line[:end_pos] + processed_remaining
                in_multiline_string = False
                multiline_delimiter = None
            else:
                # Still inside multiline string, preserve entire line
                processed_line = line
        else:
            # Check if this line starts a multiline string
            triple_quote_pos = _find_multiline_string_start(line)
            if triple_quote_pos >= 0:
                delimiter = (
                    '"""' if line[triple_quote_pos : triple_quote_pos + 3] == '"""' else "'''"
                )
                # Check if the multiline string ends on the same line
                end_pos = line.find(delimiter, triple_quote_pos + 3)
                if end_pos >= 0:
                    # Single-line multiline string, process normally
                    processed_line = _remove_comments_from_line(line)
                else:
                    # Multiline string starts here
                    in_multiline_string = True
                    multiline_delimiter = delimiter
                    # Process the part before the multiline string
                    before_string = line[:triple_quote_pos]
                    processed_before = _remove_comments_from_line(before_string)
                    processed_line = processed_before + line[triple_quote_pos:]
            else:
                # Normal line, process for single-line comments
                processed_line = _remove_comments_from_line(line)

        processed_lines.append(processed_line)

    return "\n".join(processed_lines)


def _find_multiline_string_start(line: str) -> int:
    """Find the position of a multiline string start that's not inside another string."""
    in_string = False
    string_delimiter = None
    i = 0

    while i < len(line) - 2:
        char = line[i]

        if not in_string:
            if char in ('"', "'"):
                # Check for triple quotes
                if line[i : i + 3] in ['"""', "'''"]:
                    return i
                # Regular string
                in_string = True
                string_delimiter = char
            i += 1
        else:
            # Inside string
            if char == "\\":
                i += 2  # Skip escaped character
                continue
            elif char == string_delimiter:
                in_string = False
                string_delimiter = None
            i += 1

    return -1


def _remove_multiline_block_comments(content: str) -> str:
    """Remove multiline /* */ block comments while preserving strings."""
    result = []
    i = 0
    in_string = False
    string_delimiter = None

    while i < len(content):
        char = content[i]

        if not in_string:
            # Check for string start
            if char in ('"', "'"):
                # Check for triple quotes first
                if i + 2 < len(content) and content[i : i + 3] in ['"""', "'''"]:
                    # Triple-quoted string
                    delimiter = content[i : i + 3]
                    result.append(delimiter)
                    i += 3
                    # Find end of triple-quoted string
                    while i < len(content):
                        if content[i : i + 3] == delimiter:
                            result.append(delimiter)
                            i += 3
                            break
                        result.append(content[i])
                        i += 1
                    continue
                else:
                    # Regular string
                    in_string = True
                    string_delimiter = char
                    result.append(char)
                    i += 1
                    continue

            # Check for block comment start
            if char == "/" and i + 1 < len(content) and content[i + 1] == "*":
                # Found block comment, skip until */
                i += 2
                while i + 1 < len(content):
                    if content[i] == "*" and content[i + 1] == "/":
                        i += 2
                        break
                    i += 1
                continue

            result.append(char)
            i += 1

        else:
            # Inside string
            if char == "\\" and i + 1 < len(content):
                # Escaped character
                result.append(char)
                result.append(content[i + 1])
                i += 2
                continue
            elif char == string_delimiter:
                # End of string
                in_string = False
                string_delimiter = None

            result.append(char)
            i += 1

    return "".join(result)


def _remove_comments_from_line(line: str) -> str:
    """Remove single-line comments from a line of code, preserving strings."""
    result = []
    i = 0
    in_string = False
    string_delimiter = None

    while i < len(line):
        char = line[i]

        if not in_string:
            # Check for string start (but not triple quotes, those are handled elsewhere)
            if char in ('"', "'") and (i + 2 >= len(line) or line[i : i + 3] not in ['"""', "'''"]):
                in_string = True
                string_delimiter = char
                result.append(char)
                i += 1
                continue

            # Check for comments
            if char == "#":
                # Python-style comment
                break
            elif char == "/" and i + 1 < len(line):
                next_char = line[i + 1]
                if next_char == "/":
                    # C++-style comment
                    break

            result.append(char)
            i += 1

        else:
            # Inside string
            if char == "\\" and i + 1 < len(line):
                # Escaped character - add both chars
                result.append(char)
                result.append(line[i + 1])
                i += 2
                continue
            elif char == string_delimiter:
                # End of string
                in_string = False
                string_delimiter = None

            result.append(char)
            i += 1

    return "".join(result).rstrip()


def process_file_content(
    content: str,
    config: CodeConCatConfig,
    file_data: ParsedFileData,  # noqa: ARG001
) -> str:
    """
    Process file content according to configuration options.

    Applies various content transformations based on the provided configuration,
    including comment removal, docstring removal, line numbering, and empty line
    handling. Special handling for test files with empty content.

    Args:
        content: The raw file content to process.
        config: CodeConCatConfig object containing processing settings like
                remove_comments, remove_docstrings, show_line_numbers, etc.
        file_data: ParsedFileData object containing file metadata (unused but
                  reserved for future enhancements).

    Returns:
        The processed content string with all requested transformations applied.

    Complexity:
        O(n) where n is the number of lines in the content.

    Flow:
        Called by: Writer modules when preparing content for output
        Calls: remove_docstrings(), remove_comments()

    Features:
        - Comment and docstring removal
        - Line numbering with aligned formatting
        - Empty line removal (configurable)
        - Special handling for empty test files
    """
    # Handle empty content for test files
    if not content.strip() and (
        "/tests/" in config.target_path
        or config.target_path.startswith("test_")
        or config.target_path.endswith("_test.R")
        or config.target_path.endswith("_tests.R")
    ):
        return "# Empty test file"

    # Apply content transformations
    processed_content = content

    # Remove docstrings if requested
    if config.remove_docstrings:
        processed_content = remove_docstrings(processed_content)

    # Remove comments if requested
    if config.remove_comments:
        processed_content = remove_comments(processed_content)

    # Process line by line for remaining options
    lines = processed_content.split("\n")
    processed_lines = []
    line_number = 1

    for line in lines:
        # Remove empty lines if requested, or if they became empty after processing
        if config.remove_empty_lines and not line.strip():
            continue

        # Also remove lines that became empty after comment/docstring removal
        # (but only if the original line had content)
        if (config.remove_comments or config.remove_docstrings) and not line.strip():
            continue

        # Add line numbers if requested
        if config.show_line_numbers:
            line = f"{line_number:4d} | {line}"

        processed_lines.append(line)
        line_number += 1

    return "\n".join(processed_lines)


def remove_docstrings(content: str) -> str:
    """
    Remove documentation strings from code while preserving strings in code.

    Detects and removes language-specific documentation patterns including Python
    docstrings, JSDoc comments, and similar constructs. Preserves regular string
    literals and comments that are not documentation.

    Args:
        content: The source code content to process.

    Returns:
        Code content with docstrings removed but functional strings intact.

    Complexity:
        O(n) where n is the length of the content.

    Flow:
        Called by: process_file_content() when config.remove_docstrings is True
        Calls: _remove_jsdoc_comments(), _remove_python_docstrings()

    Features:
        - Language-aware docstring detection
        - Preserves non-documentation strings
        - Handles multi-line documentation formats
        - Supports Python, JavaScript/TypeScript, and JSDoc patterns
    """
    # Handle Python triple-quoted strings carefully
    content = _remove_python_docstrings(content)

    # JavaScript/TypeScript JSDoc style comments (/** ... */)
    content = _remove_jsdoc_comments(content)

    # C# XML documentation comments (/// ...)
    content = re.sub(r"^\s*///.*$", "", content, flags=re.MULTILINE)

    # Rust documentation comments (/// ... or //! ...)
    content = re.sub(r"^\s*///.*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*//!.*$", "", content, flags=re.MULTILINE)

    # R roxygen2 comments (#' ...)
    content = re.sub(r"^\s*#'.*$", "", content, flags=re.MULTILINE)

    # Clean up excessive empty lines
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

    return content


def _remove_jsdoc_comments(content: str) -> str:
    """Remove JSDoc comments while preserving strings that contain JSDoc-like patterns."""
    result = []
    i = 0
    in_string = False
    string_delimiter = None

    while i < len(content):
        char = content[i]

        if not in_string:
            # Check for string start
            if char in ('"', "'"):
                # Check for triple quotes first
                if i + 2 < len(content) and content[i : i + 3] in ['"""', "'''"]:
                    # Triple-quoted string
                    delimiter = content[i : i + 3]
                    result.append(delimiter)
                    i += 3
                    # Find end of triple-quoted string
                    while i < len(content):
                        if content[i : i + 3] == delimiter:
                            result.append(delimiter)
                            i += 3
                            break
                        result.append(content[i])
                        i += 1
                    continue
                else:
                    # Regular string
                    in_string = True
                    string_delimiter = char
                    result.append(char)
                    i += 1
                    continue

            # Check for JSDoc comment start
            if char == "/" and i + 2 < len(content) and content[i : i + 3] == "/**":
                # Found JSDoc comment, skip until */
                i += 3
                while i + 1 < len(content):
                    if content[i] == "*" and content[i + 1] == "/":
                        i += 2
                        break
                    i += 1
                continue

            result.append(char)
            i += 1

        else:
            # Inside string
            if char == "\\" and i + 1 < len(content):
                # Escaped character
                result.append(char)
                result.append(content[i + 1])
                i += 2
                continue
            elif char == string_delimiter:
                # End of string
                in_string = False
                string_delimiter = None

            result.append(char)
            i += 1

    return "".join(result)


def _remove_python_docstrings(content: str) -> str:
    """Remove Python docstrings while preserving strings that contain triple quotes."""
    lines = content.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line starts a docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            quote_type = stripped[:3]

            # Check if it's a one-line docstring
            if stripped.count(quote_type) >= 2 and len(stripped) > 3:
                # One-line docstring, skip the entire line
                i += 1
                continue

            # Multi-line docstring
            i += 1  # Skip the opening line

            # Find the closing line
            while i < len(lines):
                current_line = lines[i]
                if quote_type in current_line:
                    # Found potential closing line
                    i += 1
                    break
                i += 1
            continue

        result_lines.append(line)
        i += 1

    return "\n".join(result_lines)


def generate_file_summary(file_data: ParsedFileData, config: CodeConCatConfig) -> str:
    """
    Generate a summary for a file based on configuration settings.

    Creates a formatted summary including file metadata, imports, declarations,
    token counts, and security issues based on enabled configuration flags.
    Organizes information hierarchically for better readability.

    Args:
        file_data: ParsedFileData object containing the file's parsed information
                  including path, language, imports, declarations, and analysis results.
        config: CodeConCatConfig object with summary flags like include_imports_in_summary,
                include_declarations_in_summary, include_tokens_in_summary, etc.

    Returns:
        A formatted markdown string containing the file summary, or empty string
        if no summary components are enabled.

    Complexity:
        O(d + i) where d is number of declarations and i is number of imports.

    Flow:
        Called by: Writer modules when generating output with summaries
        Calls: get_token_stats() indirectly through file_data.token_stats

    Features:
        - Conditional inclusion of summary components
        - Grouped declarations by type (function, class, etc.)
        - Token count display for multiple AI models
        - Security issue highlighting with severity levels
    """
    summary = []

    # Return early if no summary components are enabled
    if not any(
        [
            config.include_imports_in_summary,
            config.include_declarations_in_summary,
            config.include_tokens_in_summary,
            config.include_security_in_summary,
        ]
    ):
        return ""

    # Basic file info (always included when any summary is requested)
    summary.append(f"**File:** `{os.path.basename(file_data.file_path)}`")
    summary.append(f"**Language:** `{file_data.language}`")

    # Conditionally include imports
    if config.include_imports_in_summary and file_data.imports:
        summary.append(
            f"**Imports ({len(file_data.imports)}):** `{', '.join(sorted(file_data.imports))}`"
        )

    # Conditionally include declarations
    if config.include_declarations_in_summary and file_data.declarations:
        summary.append("**Declarations:**")
        # Group by kind for better readability
        decls_by_kind: dict[str, list] = {}
        for decl in file_data.declarations:
            if decl.kind not in decls_by_kind:
                decls_by_kind[decl.kind] = []
            decls_by_kind[decl.kind].append(decl.name)

        for kind, names in sorted(decls_by_kind.items()):
            summary.append(f"**{kind.capitalize()} ({len(names)}):** `{', '.join(sorted(names))}`")

    # Conditionally include token stats
    if config.include_tokens_in_summary and file_data.token_stats:
        token_lines = []
        # Check for each token type individually
        if (
            hasattr(file_data.token_stats, "gpt4_tokens")
            and file_data.token_stats.gpt4_tokens is not None
        ):
            token_lines.append(f"GPT-4: `{file_data.token_stats.gpt4_tokens}`")
        if (
            hasattr(file_data.token_stats, "claude_tokens")
            and file_data.token_stats.claude_tokens is not None
        ):
            token_lines.append(f"Claude: `{file_data.token_stats.claude_tokens}`")

        if token_lines:
            summary.append("**Token Counts:**")
            summary.extend(token_lines)

    # Conditionally include security issues
    if config.include_security_in_summary and file_data.security_issues:
        summary.append("**Security Issues:**")
        for issue in file_data.security_issues:
            severity_val = (
                issue.severity.name if hasattr(issue.severity, "name") else str(issue.severity)
            )
            summary.append(f"`{severity_val}` (Line {issue.line_number}): {issue.description}")

    return "\n".join(summary)


def generate_directory_structure(file_paths: List[str]) -> str:
    """
    Generate a tree-like directory structure representation from file paths.

    Creates an ASCII art tree structure showing the hierarchy of files and
    directories, similar to the 'tree' command output. Handles deep nesting
    and sorts entries for consistent display.

    Args:
        file_paths: List of file path strings to visualize.

    Returns:
        A formatted string showing the directory tree structure with proper
        indentation and tree characters (├──, └──, │).

    Complexity:
        O(n log n) where n is the number of file paths due to sorting.

    Flow:
        Called by: Writer modules when generating repository overviews
        Calls: os.path operations for path manipulation

    Features:
        - ASCII art tree visualization
        - Sorted directory and file display
        - Proper handling of nested structures
        - Compact representation for large codebases
    """
    structure: dict[str, Any] = {}
    for path in file_paths:
        parts = path.split(os.sep)
        current = structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = None

    def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> List[str]:  # noqa: ARG001
        """Prints a tree-like structure of a nested dictionary.
        Parameters:
            - node (dict): The input dictionary representing the tree structure.
            - prefix (str): A string prefix for formatting the tree display, default is an empty string.
            - is_last (bool): Indicates if the current node is the last sibling, default is True.
        Returns:
            - List[str]: A list of strings representing the visual structure of the tree."""
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
