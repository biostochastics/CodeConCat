"""Optimized JSON writer for API consumption and programmatic access."""

import json
from pathlib import Path
from typing import Any

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
from codeconcat.writer.compression_helper import CompressionHelper


def write_json(
    items: list[AnnotatedFileData | ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """
    Generate JSON output optimized for API consumption and data exchange.

    Creates a structured JSON representation of the codebase with rich metadata,
    indexes for efficient lookup, and relationship mapping. Supports compression
    segments, security annotations, and comprehensive statistics.

    Args:
        items: List of AnnotatedFileData or ParsedDocData objects containing
               parsed code files with annotations and metadata.
        config: CodeConCatConfig object with output settings including
                compression_enabled, sort_files, include_repo_overview, etc.
        folder_tree_str: Pre-generated directory tree structure string for
                        repository overview section (optional).

    Returns:
        A formatted JSON string containing the complete codebase representation
        with metadata, statistics, file contents, and relationships.

    Complexity:
        O(n log n) for sorted output where n is number of files,
        O(n) for unsorted output.

    Flow:
        Called by: Main output pipeline, API endpoints
        Calls: CompressionHelper for segment handling, rendering adapters

    Features:
        - Structured nested objects for easy traversal
        - Consistent schema with type hints
        - Metadata enrichment for filtering/searching
        - Relationship mapping between files
        - Efficient compression segment handling
        - Summary statistics for quick overview
        - Language and type indexing
        - Security issue tracking
    """

    # Check if we're in diff mode
    is_diff_mode = any(hasattr(item, "diff_metadata") and item.diff_metadata for item in items)

    # Add diff metadata if in diff mode
    diff_info = {}
    if is_diff_mode and items and hasattr(items[0], "diff_metadata") and items[0].diff_metadata:
        diff_meta = items[0].diff_metadata
        diff_info = {
            "mode": "diff",
            "from_ref": diff_meta.from_ref,
            "to_ref": diff_meta.to_ref,
            "changes": _calculate_diff_statistics(items),
        }

    output: dict[str, Any] = {
        "metadata": {
            "version": "2.0",
            "generator": "codeconcat-optimized",
            "timestamp": _get_timestamp(),
            "config": {
                "format": config.format,
                "compression_enabled": config.enable_compression,
                "sorting_enabled": config.sort_files,
            },
            **diff_info,  # Merge diff info if present
        },
        "statistics": _calculate_statistics(items),
        "repository": {},
        "files": [],
        "relationships": {},
        "indexes": {},
    }

    # Repository overview with structured data
    if config.include_repo_overview:
        output["repository"] = {
            "structure": folder_tree_str if config.include_directory_structure else None,
            "file_count": len(items),
            "categories": _categorize_files(items),
        }

    # Build indexes for efficient lookup
    indexes: dict[str, Any] = {
        "by_language": {},
        "by_type": {},
        "by_directory": {},
        "with_issues": [],
        "with_declarations": [],
    }
    output["indexes"] = indexes

    # Process files with rich metadata
    sorted_items = (
        sorted(items, key=lambda x: getattr(x, "file_path", "")) if config.sort_files else items
    )

    for item in sorted_items:
        file_data = item.render_json_dict(config)

        # Skip items that return None
        if file_data is None:
            continue

        # Enhance with additional metadata
        file_path = getattr(item, "file_path", "")
        # Sanitize path for output if configured
        sanitized_path = _sanitize_path(file_path, config)
        # If the item-provided dict includes a file_path, normalize it as well
        if isinstance(file_data, dict) and "file_path" in file_data:
            file_data["file_path"] = sanitized_path
        file_data["metadata"] = {
            "path": sanitized_path,
            "directory": _get_directory(sanitized_path),
            "filename": _get_filename(sanitized_path),
            "extension": _get_extension(sanitized_path),
            "language": getattr(item, "language", "unknown"),
            "size_bytes": len(getattr(item, "content", "").encode("utf-8")),
            "line_count": len(getattr(item, "content", "").splitlines()),
        }

        # Add analysis data if available
        if hasattr(item, "declarations") and item.declarations:
            file_data["analysis"] = {
                "declaration_count": len(item.declarations),
                "declarations": [
                    {
                        "name": d.name,
                        "type": d.kind,
                        "line_range": [d.start_line, d.end_line],
                        "children_count": len(d.children) if d.children else 0,
                    }
                    for d in item.declarations
                ],
            }
            indexes["with_declarations"].append(file_path)

        # Add security data if available
        if hasattr(item, "security_issues") and item.security_issues:
            file_data["security"] = {
                "issue_count": len(item.security_issues),
                "by_severity": _group_by_severity(item.security_issues),
                "issues": [
                    {
                        "rule": issue.rule_id,
                        "severity": issue.severity.value,
                        "line": issue.line_number,
                        "description": issue.description,
                    }
                    for issue in item.security_issues
                ],
            }
            indexes["with_issues"].append(file_path)

        # Add diff data if available
        if hasattr(item, "diff_metadata") and item.diff_metadata:
            file_data["diff"] = {
                "change_type": item.diff_metadata.change_type,
                "additions": item.diff_metadata.additions,
                "deletions": item.diff_metadata.deletions,
                "binary": item.diff_metadata.binary,
                "from_ref": item.diff_metadata.from_ref,
                "to_ref": item.diff_metadata.to_ref,
            }
            if item.diff_metadata.old_path:
                file_data["diff"]["old_path"] = item.diff_metadata.old_path
            if item.diff_metadata.similarity is not None:
                file_data["diff"]["similarity"] = item.diff_metadata.similarity

            # Include diff content if present
            if hasattr(item, "diff_content") and item.diff_content:
                file_data["diff"]["content"] = item.diff_content

        # Add compression data if enabled
        if config.enable_compression and hasattr(config, "_compressed_segments"):
            segments = CompressionHelper.extract_compressed_segments(config, file_path)
            if segments:
                file_data["compression"] = {
                    "applied": True,
                    "segment_count": len(segments),
                    "segments": [
                        CompressionHelper.format_segment_for_json(seg) for seg in segments
                    ],
                }

        # Update indexes
        language = file_data["metadata"]["language"]
        if language not in indexes["by_language"]:
            indexes["by_language"][language] = []
        indexes["by_language"][language].append(sanitized_path)

        file_type = _get_file_type(sanitized_path)
        if file_type not in indexes["by_type"]:
            indexes["by_type"][file_type] = []
        indexes["by_type"][file_type].append(sanitized_path)

        directory = file_data["metadata"]["directory"]
        if directory not in indexes["by_directory"]:
            indexes["by_directory"][directory] = []
        indexes["by_directory"][directory].append(sanitized_path)

        # Store the enhanced file data in array format for compatibility
        output["files"].append(file_data)

    # Build relationships between files (use sanitized paths for keys)
    output["relationships"] = _build_relationships(sorted_items, config)

    # Convert to JSON with proper formatting
    indent = getattr(config, "json_indent", 2)
    return json.dumps(output, indent=indent, default=str, ensure_ascii=False)


def _get_timestamp() -> str:
    """Get ISO format timestamp."""
    from datetime import datetime

    return datetime.now().isoformat()


def _calculate_statistics(items: list[AnnotatedFileData | ParsedDocData]) -> dict[str, Any]:
    """Calculate comprehensive statistics."""
    total_lines = sum(len(getattr(i, "content", "").splitlines()) for i in items)
    total_size = sum(len(getattr(i, "content", "").encode("utf-8")) for i in items)

    return {
        "total_files": len(items),
        "total_lines": total_lines,
        "total_bytes": total_size,
        "languages": list({getattr(i, "language", "unknown") for i in items}),
        "average_file_size": total_size // len(items) if items else 0,
    }


def _calculate_diff_statistics(
    items: list[AnnotatedFileData | ParsedDocData],
) -> dict[str, Any]:
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


def _categorize_files(items: list[AnnotatedFileData | ParsedDocData]) -> dict[str, int]:
    """Categorize files by type."""
    categories = {"source": 0, "test": 0, "documentation": 0, "configuration": 0, "other": 0}

    for item in items:
        path = getattr(item, "file_path", "").lower()
        if "test" in path or "spec" in path:
            categories["test"] += 1
        elif path.endswith((".md", ".rst", ".txt")):
            categories["documentation"] += 1
        elif path.endswith((".json", ".yml", ".yaml", ".toml", ".ini")):
            categories["configuration"] += 1
        elif any(path.endswith(ext) for ext in (".py", ".js", ".ts", ".java", ".cpp", ".go")):
            categories["source"] += 1
        else:
            categories["other"] += 1

    return categories


def _get_directory(file_path: str) -> str:
    """Extract directory from file path."""
    import os

    return os.path.dirname(file_path) or "."


def _get_filename(file_path: str) -> str:
    """Extract filename from file path."""
    import os

    return os.path.basename(file_path)


def _get_extension(file_path: str) -> str:
    """Extract extension from file path."""
    import os

    ext = os.path.splitext(file_path)[1]
    return ext[1:] if ext else ""


def _get_file_type(file_path: str) -> str:
    """Determine file type from path."""
    path = file_path.lower()
    if "test" in path or "spec" in path:
        return "test"
    elif path.endswith((".md", ".rst", ".txt")):
        return "documentation"
    elif path.endswith((".json", ".yml", ".yaml", ".toml", ".ini")):
        return "configuration"
    elif any(path.endswith(ext) for ext in (".py", ".js", ".ts", ".java", ".cpp", ".go")):
        return "source"
    else:
        return "other"


def _group_by_severity(issues: list[Any]) -> dict[str, int]:
    """Group security issues by severity."""
    severity_counts: dict[str, int] = {}
    for issue in issues:
        severity = str(issue.severity.value)
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return severity_counts


def _build_relationships(
    items: list[AnnotatedFileData | ParsedDocData],
    config: CodeConCatConfig,
) -> dict[str, Any]:
    """Build relationships between files based on imports and references.

    Uses sanitized (possibly relative) paths as keys when config.redact_paths is enabled.
    """
    relationships: dict[str, Any] = {"imports": {}, "imported_by": {}, "references": {}}

    for item in items:
        if hasattr(item, "imports") and item.imports:
            original_path = getattr(item, "file_path", "")
            sanitized_path = _sanitize_path(original_path, config)

            # Sanitize all import paths to prevent leaking absolute paths
            sanitized_imports = [_sanitize_path(imp, config) for imp in item.imports]
            relationships["imports"][sanitized_path] = sanitized_imports

            # Build reverse mapping with sanitized paths
            for imp in sanitized_imports:
                if imp not in relationships["imported_by"]:
                    relationships["imported_by"][imp] = []
                relationships["imported_by"][imp].append(sanitized_path)

    return relationships


def _sanitize_path(file_path: str, config: CodeConCatConfig) -> str:
    """Sanitize a file path for output based on configuration.

    - If config.redact_paths is False, return the path unchanged.
    - If the path is absolute, attempt to make it relative to config.target_path or cwd.
    - As a last resort, return the last two path components to avoid leaking user directories.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        if not getattr(config, "redact_paths", False):
            return file_path

        if not file_path:
            return file_path

        p = Path(file_path)
        # If already relative, return as-is
        if not p.is_absolute():
            return file_path

        # Try relative to configured target path first
        try:
            base = Path(getattr(config, "target_path", ".")).resolve()
        except Exception as e:
            logger.debug(f"Failed to resolve target_path, using cwd: {e}")
            base = Path.cwd()

        try:
            rel = p.resolve().relative_to(base)
            return rel.as_posix()
        except ValueError:
            # Try making it relative to the current working directory
            try:
                rel2 = p.resolve().relative_to(Path.cwd())
                return rel2.as_posix()
            except ValueError:
                # Fallback: keep only the last 2 components
                parts = p.parts
                if len(parts) >= 2:
                    logger.debug(
                        f"Path redaction fallback: keeping last 2 components of {file_path}"
                    )
                    return "/".join(parts[-2:])
                return p.name
    except Exception as e:
        # On any unexpected error, log it and return the original path
        logger.warning(f"Failed to sanitize path '{file_path}': {e}. Using original path.")
        return file_path
