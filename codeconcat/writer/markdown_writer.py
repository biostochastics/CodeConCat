"""Optimized Markdown writer for human readability with navigation."""

import os
import re
from typing import List

from codeconcat.base_types import CodeConCatConfig, Declaration, WritableItem


def write_markdown(
    items: List[WritableItem],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """
    Generate Markdown output optimized for human readability with navigation.

    Creates a comprehensive Markdown document with table of contents, anchor links,
    syntax highlighting, and rich formatting. Designed for code review, documentation,
    and human consumption with emphasis on navigation and readability.

    Args:
        items: List of WritableItem objects (AnnotatedFileData or ParsedDocData)
               containing parsed code files with annotations.
        config: CodeConCatConfig object with output settings including
                sort_files, include_repo_overview, include_directory_structure, etc.
        folder_tree_str: Pre-generated directory tree structure string for
                        repository overview section (optional).

    Returns:
        A formatted Markdown string with complete codebase documentation including
        TOC, file contents, cross-references, and statistics.

    Complexity:
        O(n log n) for sorted output where n is number of files,
        O(n) for unsorted output.

    Flow:
        Called by: Main output pipeline, documentation generators
        Calls: CompressionHelper for segment handling, rendering adapters

    Features:
        - Table of contents with anchor links
        - Section numbering for easy reference
        - Cross-references between related files
        - Syntax highlighting for all code blocks
        - Collapsible sections for large content
        - Summary statistics and metrics
        - Language-aware code formatting
        - Security issue highlighting
    """

    output_parts = []

    # Title and metadata
    output_parts.append("# CodeConCat Analysis Report\n")
    output_parts.append(f"**Generated**: {_get_timestamp()}\n")
    output_parts.append(f"**Total Files**: {len(items)}\n")

    # Check if AI summarization is enabled
    ai_summaries_count = sum(1 for item in items if hasattr(item, "ai_summary") and item.ai_summary)
    if ai_summaries_count > 0:
        output_parts.append(
            f"**AI Summaries**: Enabled ({ai_summaries_count}/{len(items)} files)\n"
        )
    elif getattr(config, "enable_ai_summary", False):
        output_parts.append("**AI Summaries**: Enabled but no summaries generated\n")

    output_parts.append("")

    # Table of Contents with anchor links
    output_parts.append("## Table of Contents\n")
    output_parts.append("- [Project Overview](#project-overview)")
    output_parts.append("- [Directory Structure](#directory-structure)")
    output_parts.append("- [File Index](#file-index)")
    output_parts.append("- [File Details](#file-details)")

    # Add file-specific TOC entries
    sorted_items = (
        sorted(items, key=lambda x: getattr(x, "file_path", "")) if config.sort_files else items
    )
    for i, item in enumerate(sorted_items, 1):
        file_path = getattr(item, "file_path", "")
        anchor = _create_anchor(file_path)
        output_parts.append(f"  - [{i}. {file_path}](#{anchor})")

    output_parts.append("")
    output_parts.append("---\n")

    # Project Overview Section
    output_parts.append("## Project Overview {#project-overview}\n")

    if config.include_repo_overview:
        # Add summary statistics
        output_parts.append("### Summary Statistics\n")
        stats = _calculate_statistics(items)
        output_parts.append("| Metric | Value |")
        output_parts.append("|--------|-------|")
        for key, value in stats.items():
            output_parts.append(f"| {key} | {value} |")
        output_parts.append("")

        # Directory Structure with collapsible details
        if config.include_directory_structure and folder_tree_str:
            output_parts.append("### Directory Structure {#directory-structure}\n")
            output_parts.append("<details>")
            output_parts.append("<summary>Click to expand directory tree</summary>\n")
            output_parts.append("```")
            output_parts.append(folder_tree_str)
            output_parts.append("```")
            output_parts.append("</details>\n")

    # File Index with categorization
    if config.include_file_index:
        output_parts.append("## File Index {#file-index}\n")

        # Categorize files
        categories = _categorize_files(sorted_items)

        for category, files in categories.items():
            if files:
                output_parts.append(f"### {category}\n")
                output_parts.append("| # | File | Type | Size |")
                output_parts.append("|---|------|------|------|")

                for i, item in enumerate(files, 1):
                    file_path = getattr(item, "file_path", "")
                    anchor = _create_anchor(file_path)
                    file_type = _get_file_type(file_path)
                    size = _estimate_size(item)
                    output_parts.append(
                        f"| {i} | [{file_path}](#{anchor}) | {file_type} | {size} |"
                    )
                output_parts.append("")

    output_parts.append("---\n")

    # File Details Section
    output_parts.append("## File Details {#file-details}\n")

    for i, item in enumerate(sorted_items, 1):
        file_path = getattr(item, "file_path", "")
        anchor = _create_anchor(file_path)

        # File header with anchor
        output_parts.append(f"### {i}. {file_path} {{#{anchor}}}\n")

        # Add navigation links
        output_parts.append("[↑ Back to TOC](#table-of-contents) | ")
        if i > 1:
            prev_file_path = getattr(sorted_items[i - 2], "file_path", "")
            prev_anchor = _create_anchor(prev_file_path)
            output_parts.append(f"[← Previous](#{prev_anchor}) | ")
        if i < len(sorted_items):
            next_file_path = getattr(sorted_items[i], "file_path", "")
            next_anchor = _create_anchor(next_file_path)
            output_parts.append(f"[Next →](#{next_anchor})")
        output_parts.append("\n")

        # AI Summary section if available
        if hasattr(item, "ai_summary") and item.ai_summary:
            output_parts.append("#### AI Summary\n")
            output_parts.append(f"> {item.ai_summary}\n")
            output_parts.append("")

        # File metadata in a table
        if config.include_file_summary:
            output_parts.append("#### File Information\n")
            output_parts.append("| Property | Value |")
            output_parts.append("|----------|-------|")
            output_parts.append(f"| Language | {getattr(item, 'language', 'Unknown')} |")
            output_parts.append(f"| Lines | {_count_lines(item)} |")

            # Declarations summary
            if hasattr(item, "declarations") and item.declarations:
                output_parts.append(f"| Functions/Classes | {len(item.declarations)} |")

            # Security summary
            if hasattr(item, "security_issues") and item.security_issues:
                output_parts.append(f"| Security Issues | {len(item.security_issues)} |")

            # AI Summary indicator
            if hasattr(item, "ai_summary") and item.ai_summary:
                output_parts.append("| AI Summary | Available |")

            output_parts.append("")

            # Detailed declarations with collapsible
            if hasattr(item, "declarations") and item.declarations:
                output_parts.append("<details>")
                output_parts.append("<summary>📦 Declarations</summary>\n")
                output_parts.append(_render_declarations_tree(item.declarations))
                output_parts.append("</details>\n")

            # Security issues with severity badges
            if hasattr(item, "security_issues") and item.security_issues:
                output_parts.append("<details>")
                output_parts.append("<summary>⚠️ Security Issues</summary>\n")
                for issue in item.security_issues:
                    severity_badge = _get_severity_badge(issue.severity)
                    output_parts.append(
                        f"- {severity_badge} **Line {issue.line_number}**: {issue.description}"
                    )
                output_parts.append("\n</details>\n")

        # File content with syntax highlighting
        output_parts.append("#### Source Code\n")
        language = getattr(item, "language", "")
        content = getattr(item, "content", "")

        # Add line numbers if configured
        if config.show_line_numbers:
            content = _add_line_numbers(content)

        output_parts.append(f"```{language}")
        output_parts.append(content)
        output_parts.append("```\n")

        output_parts.append("---\n")

    # Footer with generation info
    output_parts.append("\n---\n")
    output_parts.append("*Generated by CodeConCat - Optimized for human review*\n")

    return "\n".join(output_parts)


def _create_anchor(file_path: str) -> str:
    """Create a URL-safe anchor from a file path."""
    # Remove leading ./ and convert to lowercase
    anchor = file_path.lstrip("./").lower()
    # Replace non-alphanumeric with hyphens
    anchor = re.sub(r"[^a-z0-9]+", "-", anchor)
    # Remove leading/trailing hyphens
    return anchor.strip("-")


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _calculate_statistics(items: List[WritableItem]) -> dict:
    """Calculate summary statistics."""
    stats = {
        "Total Files": len(items),
        "Source Files": sum(
            1 for i in items if not getattr(i, "file_path", "").endswith((".md", ".txt", ".rst"))
        ),
        "Documentation Files": sum(
            1 for i in items if getattr(i, "file_path", "").endswith((".md", ".txt", ".rst"))
        ),
        "Total Lines": sum(_count_lines(i) for i in items),
    }
    return stats


def _categorize_files(items: List[WritableItem]) -> dict:
    """Categorize files by type."""
    categories: dict[str, list] = {
        "Source Code": [],
        "Tests": [],
        "Documentation": [],
        "Configuration": [],
        "Other": [],
    }

    for item in items:
        file_path = getattr(item, "file_path", "")
        path = file_path.lower()
        if "test" in path or "spec" in path:
            categories["Tests"].append(item)
        elif path.endswith((".md", ".rst", ".txt")):
            categories["Documentation"].append(item)
        elif path.endswith((".json", ".yml", ".yaml", ".toml", ".ini")):
            categories["Configuration"].append(item)
        elif path.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c", ".go")):
            categories["Source Code"].append(item)
        else:
            categories["Other"].append(item)

    return categories


def _get_file_type(file_path: str) -> str:
    """Get file type from extension."""
    ext = os.path.splitext(file_path)[1]
    return ext[1:].upper() if ext else "Unknown"


def _estimate_size(item: WritableItem) -> str:
    """Estimate file size."""
    content = getattr(item, "content", "")
    size_bytes = len(content.encode("utf-8"))
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _count_lines(item: WritableItem) -> int:
    """Count lines in content."""
    content = getattr(item, "content", "")
    return len(content.splitlines())


def _render_declarations_tree(declarations: List[Declaration], indent: int = 0) -> str:
    """Render declarations as a tree."""
    result = []
    for decl in declarations:
        prefix = "  " * indent + "- "
        result.append(
            f"{prefix}**{decl.kind}** `{decl.name}` (lines {decl.start_line}-{decl.end_line})"
        )
        if decl.children:
            result.append(_render_declarations_tree(decl.children, indent + 1))
    return "\n".join(result)


def _get_severity_badge(severity) -> str:
    """Get severity badge emoji."""
    badges = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "ℹ️"}
    return badges.get(str(severity.value).upper(), "❓")


def _add_line_numbers(content: str) -> str:
    """Add line numbers to content."""
    lines = content.splitlines()
    numbered = []
    for i, line in enumerate(lines, 1):
        numbered.append(f"{i:4d} | {line}")
    return "\n".join(numbered)
