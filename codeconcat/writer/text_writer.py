"""Optimized Text writer for terminal and CLI usage."""

import textwrap
from collections.abc import Sequence
from typing import Any

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData, WritableItem

# Terminal width constants
TERM_WIDTH = 80
SEPARATOR_CHAR = "="
SUBSEPARATOR_CHAR = "-"


def write_text(
    items: list[AnnotatedFileData | ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """
    Generate text output optimized for terminal display and CLI usage.

    Creates a structured plain text representation with proper formatting for
    terminal display. Includes visual separators, tree structures, and wrapped
    text optimized for 80-character terminal width. Ideal for CLI tools, logs,
    and terminal-based code review.

    Args:
        items: List of WritableItem objects (AnnotatedFileData or ParsedDocData)
               containing parsed code files with annotations.
        config: CodeConCatConfig object with output settings including
                include_repo_overview, include_file_index, sort_files, etc.
        folder_tree_str: Pre-generated directory tree structure string for
                        repository overview section (optional).

    Returns:
        A formatted plain text string with visual hierarchy, wrapped at 80
        characters, containing file contents and metadata.

    Complexity:
        O(n log n) for sorted output where n is number of files,
        O(n) for unsorted output.

    Flow:
        Called by: CLI interface, terminal output handlers
        Calls: CompressionHelper for segment handling, text wrapping utilities

    Features:
        - Proper line wrapping for terminal width (80 chars)
        - Visual hierarchy with box drawing characters
        - ASCII art separators and headers
        - Tree-style file listing
        - Compact mode for quick overview
        - Line number preservation
        - Security issue annotations
    """

    output_lines = []

    # Check if we're in diff mode
    is_diff_mode = any(hasattr(item, "diff_metadata") and item.diff_metadata for item in items)

    # Header with box drawing - adjust for diff mode
    if is_diff_mode and items and hasattr(items[0], "diff_metadata") and items[0].diff_metadata:
        diff_meta = items[0].diff_metadata
        header_title = f"DIFF: {diff_meta.from_ref[:7]}...{diff_meta.to_ref[:7]}"
    else:
        header_title = "CODECONCAT OUTPUT"

    output_lines.append(_create_header(header_title))
    output_lines.append("")

    # Summary section
    output_lines.append(_create_section_header("SUMMARY"))
    stats = _calculate_statistics(items)
    for key, value in stats.items():
        output_lines.append(f"  {key}: {value}")

    # Add diff-specific statistics if in diff mode
    if is_diff_mode:
        diff_stats = _calculate_diff_statistics(items)
        output_lines.append("")
        output_lines.append("  Changes:")
        output_lines.append(f"    Added:    +{diff_stats['total_additions']} lines")
        output_lines.append(f"    Deleted:  -{diff_stats['total_deletions']} lines")
        output_lines.append(
            f"    Files:    {diff_stats['files_added']} added, "
            f"{diff_stats['files_modified']} modified, "
            f"{diff_stats['files_deleted']} deleted"
        )

    output_lines.append("")

    # Repository structure
    if config.include_repo_overview:
        output_lines.append(_create_section_header("PROJECT STRUCTURE"))

        if config.include_directory_structure and folder_tree_str:
            # Indent the tree for better visual hierarchy
            for line in folder_tree_str.splitlines():
                output_lines.append(f"  {line}")
        else:
            # Create a simple tree from file paths
            tree = _build_file_tree(items)
            output_lines.extend(_render_tree(tree, indent=2))
        output_lines.append("")

    # File index with visual indicators
    if config.include_file_index:
        output_lines.append(_create_section_header("FILE INDEX"))

        sorted_items = sorted(items, key=lambda x: x.file_path) if config.sort_files else items

        for i, item in enumerate(sorted_items, 1):
            # Add visual indicators for file types
            indicator = _get_file_indicator(item.file_path)
            size = _format_size(len(getattr(item, "content", "")))
            output_lines.append(f"  {i:3d}. {indicator} {item.file_path} ({size})")

        output_lines.append("")
        output_lines.append("  Legend: 📝=source 🧪=test 📄=doc ⚙️=config 📦=other")
        output_lines.append("")

    # Files section with proper formatting
    output_lines.append(_create_section_header("FILES"))
    output_lines.append("")

    sorted_items = sorted(items, key=lambda x: x.file_path) if config.sort_files else items

    for i, item in enumerate(sorted_items):
        # File header with visual separator
        output_lines.append(_create_file_header(item.file_path, i + 1, len(sorted_items)))

        # File metadata in a compact format
        if config.include_file_summary:
            metadata = _get_file_metadata(item)

            # Add diff information if available
            if hasattr(item, "diff_metadata") and item.diff_metadata:
                if not metadata:
                    metadata = {}
                diff_meta = item.diff_metadata
                metadata["Change Type"] = diff_meta.change_type.upper()
                if diff_meta.additions or diff_meta.deletions:
                    metadata["Lines Changed"] = f"+{diff_meta.additions} / -{diff_meta.deletions}"
                if diff_meta.old_path:
                    metadata["Renamed From"] = diff_meta.old_path
                if diff_meta.binary:
                    metadata["Binary File"] = "Yes"

            if metadata:
                output_lines.append("")
                output_lines.append("  Metadata:")
                for key, value in metadata.items():
                    output_lines.append(f"    {key}: {value}")
                output_lines.append("")

        # File content with optional line numbers or diff
        if hasattr(item, "diff_content") and item.diff_content:
            # Show diff content instead of regular content
            output_lines.append("  Diff:")
            output_lines.append("  " + SUBSEPARATOR_CHAR * (TERM_WIDTH - 4))

            # Split diff content into lines and format
            for line in item.diff_content.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    output_lines.append(f"  + {line[1:]}")  # Added line
                elif line.startswith("-") and not line.startswith("---"):
                    output_lines.append(f"  - {line[1:]}")  # Deleted line
                elif line.startswith("@@"):
                    output_lines.append(f"  {line}")  # Hunk header
                else:
                    output_lines.append(f"    {line}")  # Context line

            output_lines.append("")
            # Skip regular content rendering for diff mode
            continue

        output_lines.append("  Content:")
        output_lines.append("  " + SUBSEPARATOR_CHAR * (TERM_WIDTH - 4))

        content_lines = item.render_text_lines(config)

        # Add line numbers if configured
        if config.show_line_numbers:
            for line_no, line in enumerate(content_lines, 1):
                # Wrap long lines
                if len(line) > TERM_WIDTH - 10:
                    wrapped = textwrap.wrap(line, width=TERM_WIDTH - 10)
                    output_lines.append(f"  {line_no:4d} │ {wrapped[0]}")
                    for continuation in wrapped[1:]:
                        output_lines.append(f"       │ {continuation}")
                else:
                    output_lines.append(f"  {line_no:4d} │ {line}")
        else:
            for line in content_lines:
                # Wrap long lines
                if len(line) > TERM_WIDTH - 4:
                    wrapped = textwrap.wrap(line, width=TERM_WIDTH - 4)
                    for wrapped_line in wrapped:
                        output_lines.append(f"  {wrapped_line}")
                else:
                    output_lines.append(f"  {line}")

        output_lines.append("")

    # Footer
    output_lines.append(_create_footer())

    return "\n".join(output_lines)


def _create_header(title: str) -> str:
    """Create a centered header with box drawing."""
    padding = (TERM_WIDTH - len(title) - 2) // 2
    header = "╔" + "═" * (TERM_WIDTH - 2) + "╗\n"
    header += "║" + " " * padding + title + " " * (TERM_WIDTH - padding - len(title) - 2) + "║\n"
    header += "╚" + "═" * (TERM_WIDTH - 2) + "╝"
    return header


def _create_section_header(title: str) -> str:
    """Create a section header."""
    return f"▶ {title} " + SEPARATOR_CHAR * (TERM_WIDTH - len(title) - 3)


def _create_file_header(file_path: str, current: int, total: int) -> str:
    """Create a file header with progress indicator."""
    progress = f"[{current}/{total}]"
    available = TERM_WIDTH - len(progress) - 3

    if len(file_path) > available:
        # Truncate long paths
        file_path = "..." + file_path[-(available - 3) :]

    header = (
        f"▼ {file_path} " + SUBSEPARATOR_CHAR * (available - len(file_path) - 1) + f" {progress}"
    )
    return header


def _create_footer() -> str:
    """Create a footer."""
    footer = SEPARATOR_CHAR * TERM_WIDTH + "\n"
    footer += "Generated by CodeConCat - Optimized for Terminal Display"
    return footer


def _calculate_statistics(items: Sequence[WritableItem]) -> dict:
    """Calculate summary statistics."""
    total_lines = sum(len(getattr(i, "content", "").splitlines()) for i in items)
    total_size = sum(len(getattr(i, "content", "").encode("utf-8")) for i in items)

    return {
        "Files": len(items),
        "Total Lines": f"{total_lines:,}",
        "Total Size": _format_size(total_size),
        "Languages": len({getattr(i, "language", "unknown") for i in items}),
    }


def _calculate_diff_statistics(items: Sequence[WritableItem]) -> dict:
    """Calculate statistics for diff mode.

    Aggregates change statistics across all items with diff metadata to provide
    a comprehensive overview of modifications between Git references.

    Args:
        items: List of items potentially containing diff metadata

    Returns:
        Dictionary containing aggregated diff statistics including total changes,
        file categorization by change type, and line-level modifications.
    """
    stats = {
        "total_additions": 0,
        "total_deletions": 0,
        "files_added": 0,
        "files_modified": 0,
        "files_deleted": 0,
        "files_renamed": 0,
        "binary_files": 0,
    }

    for item in items:
        if hasattr(item, "diff_metadata") and item.diff_metadata:
            meta = item.diff_metadata
            stats["total_additions"] += meta.additions
            stats["total_deletions"] += meta.deletions

            if meta.binary:
                stats["binary_files"] += 1

            if meta.change_type == "added":
                stats["files_added"] += 1
            elif meta.change_type == "modified":
                stats["files_modified"] += 1
            elif meta.change_type == "deleted":
                stats["files_deleted"] += 1
            elif meta.change_type == "renamed":
                stats["files_renamed"] += 1

    return stats


def _get_file_indicator(file_path: str) -> str:
    """Get visual indicator for file type."""
    path = file_path.lower()
    if "test" in path or "spec" in path:
        return "🧪"
    elif path.endswith((".md", ".rst", ".txt")):
        return "📄"
    elif path.endswith((".json", ".yml", ".yaml", ".toml", ".ini")):
        return "⚙️"
    elif any(path.endswith(ext) for ext in (".py", ".js", ".ts", ".java", ".cpp", ".go")):
        return "📝"
    else:
        return "📦"


def _format_size(size_bytes: int) -> str:
    """Format size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _get_file_metadata(item: WritableItem) -> dict:
    """Extract metadata from file item."""
    metadata = {}

    if hasattr(item, "language"):
        metadata["Language"] = item.language

    if hasattr(item, "declarations") and item.declarations:
        metadata["Declarations"] = len(item.declarations)

    if hasattr(item, "security_issues") and item.security_issues:
        metadata["Security Issues"] = len(item.security_issues)

    if hasattr(item, "imports") and item.imports:
        metadata["Imports"] = len(item.imports)

    return metadata


def _build_file_tree(items: Sequence[WritableItem]) -> dict:
    """Build a tree structure from file paths."""
    tree: dict[str, Any] = {}

    for item in items:
        file_path = getattr(item, "file_path", "")
        parts = file_path.split("/")
        current = tree

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Add file as leaf
        current[parts[-1]] = None

    return tree


def _render_tree(tree: dict, indent: int = 0, prefix: str = "") -> list[str]:
    """Render tree structure with box drawing characters."""
    lines = []
    items = list(tree.items())

    for i, (name, subtree) in enumerate(items):
        is_last = i == len(items) - 1

        # Determine the connector
        connector = "└── " if is_last else "├── "
        lines.append(" " * indent + prefix + connector + name)

        # Recurse for directories
        if subtree is not None:
            extension = "    " if is_last else "│   "
            lines.extend(_render_tree(subtree, indent, prefix + extension))

    return lines
