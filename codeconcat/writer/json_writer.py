"""Optimized JSON writer for API consumption and programmatic access."""

import json
from typing import Any, Dict, List, Union

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
from codeconcat.writer.compression_helper import CompressionHelper


def write_json(
    items: List[Union[AnnotatedFileData, ParsedDocData]],
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

    output: Dict[str, Any] = {
        "metadata": {
            "version": "2.0",
            "generator": "codeconcat-optimized",
            "timestamp": _get_timestamp(),
            "config": {
                "format": config.format,
                "compression_enabled": config.enable_compression,
                "sorting_enabled": config.sort_files,
            },
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
    indexes: Dict[str, Any] = {
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
        file_data["metadata"] = {
            "path": file_path,
            "directory": _get_directory(file_path),
            "filename": _get_filename(file_path),
            "extension": _get_extension(file_path),
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
        indexes["by_language"][language].append(file_path)

        file_type = _get_file_type(file_path)
        if file_type not in indexes["by_type"]:
            indexes["by_type"][file_type] = []
        indexes["by_type"][file_type].append(file_path)

        directory = file_data["metadata"]["directory"]
        if directory not in indexes["by_directory"]:
            indexes["by_directory"][directory] = []
        indexes["by_directory"][directory].append(file_path)

        # Store the enhanced file data in array format for compatibility
        output["files"].append(file_data)

    # Build relationships between files
    output["relationships"] = _build_relationships(sorted_items)

    # Convert to JSON with proper formatting
    indent = getattr(config, "json_indent", 2)
    return json.dumps(output, indent=indent, default=str, ensure_ascii=False)


def _get_timestamp() -> str:
    """Get ISO format timestamp."""
    from datetime import datetime

    return datetime.now().isoformat()


def _calculate_statistics(items: List[Union[AnnotatedFileData, ParsedDocData]]) -> Dict[str, Any]:
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


def _categorize_files(items: List[Union[AnnotatedFileData, ParsedDocData]]) -> Dict[str, int]:
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


def _group_by_severity(issues: List[Any]) -> Dict[str, int]:
    """Group security issues by severity."""
    severity_counts: Dict[str, int] = {}
    for issue in issues:
        severity = str(issue.severity.value)
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return severity_counts


def _build_relationships(items: List[Union[AnnotatedFileData, ParsedDocData]]) -> Dict[str, Any]:
    """Build relationships between files based on imports and references."""
    relationships: Dict[str, Any] = {"imports": {}, "imported_by": {}, "references": {}}

    for item in items:
        if hasattr(item, "imports") and item.imports:
            file_path = getattr(item, "file_path", "")
            relationships["imports"][file_path] = item.imports

            # Build reverse mapping
            for imp in item.imports:
                if imp not in relationships["imported_by"]:
                    relationships["imported_by"][imp] = []
                relationships["imported_by"][imp].append(file_path)

    return relationships
