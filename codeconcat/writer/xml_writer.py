"""Optimized XML writer for LLM ingestion with semantic navigation."""

import xml.etree.ElementTree as ET
from xml.dom import minidom

from codeconcat.base_types import CodeConCatConfig, WritableItem
from codeconcat.writer.compression_helper import CompressionHelper


def _get_decl_attr(decl, attr: str, default=None):
    """Safely get attribute from declaration (handles both dict and object)."""
    if isinstance(decl, dict):
        return decl.get(attr, default)
    return getattr(decl, attr, default)


def _get_issue_attr(issue, attr: str, default=None):
    """Safely get attribute from security issue (handles both dict and object)."""
    if isinstance(issue, dict):
        return issue.get(attr, default)
    return getattr(issue, attr, default)


def write_xml(
    items: list[WritableItem],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    """Generate XML output optimized for LLM ingestion with semantic navigation.

    Key optimizations for LLM processing:
    - Clear semantic sections with descriptive tags
    - Hierarchical navigation structure
    - Metadata-rich elements for context understanding
    - Consistent tagging for pattern recognition
    - Explicit relationships between files
    """

    # Create root with clear semantic name for LLMs
    root = ET.Element("codebase_analysis")

    # Check if we're in diff mode
    is_diff_mode = any(hasattr(item, "diff_metadata") and item.diff_metadata for item in items)

    # Add metadata section for LLM context
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "total_files").text = str(len(items))

    # Set analysis type based on mode
    if is_diff_mode:
        ET.SubElement(metadata, "analysis_type").text = "differential"

        # Add diff-specific metadata
        if items and hasattr(items[0], "diff_metadata") and items[0].diff_metadata:
            diff_meta = items[0].diff_metadata
            diff_info = ET.SubElement(metadata, "diff_info")
            ET.SubElement(diff_info, "from_ref").text = diff_meta.from_ref
            ET.SubElement(diff_info, "to_ref").text = diff_meta.to_ref

            # Calculate diff statistics
            stats = _calculate_diff_statistics(items)
            diff_stats = ET.SubElement(diff_info, "statistics")
            ET.SubElement(diff_stats, "additions").text = str(stats["total_additions"])
            ET.SubElement(diff_stats, "deletions").text = str(stats["total_deletions"])
            ET.SubElement(diff_stats, "files_added").text = str(stats["files_added"])
            ET.SubElement(diff_stats, "files_modified").text = str(stats["files_modified"])
            ET.SubElement(diff_stats, "files_deleted").text = str(stats["files_deleted"])
            ET.SubElement(diff_stats, "files_renamed").text = str(stats["files_renamed"])
    else:
        ET.SubElement(metadata, "analysis_type").text = "full_codebase"

    # Navigation section with clear hierarchy
    if config.include_repo_overview:
        navigation = ET.SubElement(root, "navigation")

        # Project structure for spatial understanding
        if config.include_directory_structure and folder_tree_str:
            structure = ET.SubElement(navigation, "project_structure")
            structure.text = folder_tree_str

        # File index with semantic grouping
        if config.include_file_index:
            index = ET.SubElement(navigation, "file_index")

            # Group files by type for better LLM comprehension
            source_files = ET.SubElement(index, "source_files")
            doc_files = ET.SubElement(index, "documentation_files")
            config_files = ET.SubElement(index, "configuration_files")
            test_files = ET.SubElement(index, "test_files")

            sorted_items = (
                sorted(items, key=lambda x: getattr(x, "file_path", ""))
                if config.sort_files
                else items
            )

            for item in sorted_items:
                path = getattr(item, "file_path", "")
                file_elem = ET.Element("file", path=path)

                # Categorize files for semantic grouping
                if "test" in path.lower() or "spec" in path.lower():
                    test_files.append(file_elem)
                elif path.endswith((".md", ".rst", ".txt")):
                    doc_files.append(file_elem)
                elif path.endswith((".json", ".yml", ".yaml", ".toml", ".ini")):
                    config_files.append(file_elem)
                else:
                    source_files.append(file_elem)

    # Main content section with clear semantic boundaries
    content = ET.SubElement(root, "codebase_content")

    # Add instructions for LLM processing (if enabled)
    if config.xml_processing_instructions:
        instructions = ET.SubElement(content, "processing_instructions")
        instructions.text = """
        This XML contains a structured codebase analysis.
        Navigate using the <navigation> section to understand project structure.
        Each <file_entry> contains complete file information with metadata.
        Use <relationships> to understand dependencies between files.
        Security issues and important patterns are marked in <analysis> sections.
        """

    # Process files with rich semantic markup
    files_section = ET.SubElement(content, "files")
    sorted_items = (
        sorted(items, key=lambda x: getattr(x, "file_path", "")) if config.sort_files else items
    )

    for item in sorted_items:
        # Create semantically rich file entry
        file_entry = ET.SubElement(files_section, "file_entry")

        # File metadata for context
        file_meta = ET.SubElement(file_entry, "file_metadata")
        ET.SubElement(file_meta, "path").text = getattr(item, "file_path", "")
        ET.SubElement(file_meta, "language").text = getattr(item, "language", "unknown")

        # Include AI summary if available
        if hasattr(item, "ai_summary") and item.ai_summary:
            ET.SubElement(file_meta, "ai_summary").text = item.ai_summary
        # Include regular summary
        if hasattr(item, "summary") and item.summary:
            ET.SubElement(file_meta, "summary").text = item.summary

        # Add diff metadata if available
        if hasattr(item, "diff_metadata") and item.diff_metadata:
            diff_elem = ET.SubElement(file_meta, "diff")
            diff_elem.set("change_type", item.diff_metadata.change_type)
            diff_elem.set("additions", str(item.diff_metadata.additions))
            diff_elem.set("deletions", str(item.diff_metadata.deletions))
            diff_elem.set("binary", str(item.diff_metadata.binary).lower())

            if item.diff_metadata.old_path:
                diff_elem.set("old_path", item.diff_metadata.old_path)
            if item.diff_metadata.similarity is not None:
                diff_elem.set("similarity", str(item.diff_metadata.similarity))

        # File analysis section
        if config.include_file_summary:
            analysis = ET.SubElement(file_entry, "analysis")

            # Add declarations with semantic grouping
            if hasattr(item, "declarations") and item.declarations:
                declarations = ET.SubElement(analysis, "declarations")
                for decl in item.declarations:
                    start_line = _get_decl_attr(decl, "start_line", 0)
                    end_line = _get_decl_attr(decl, "end_line", 0)
                    ET.SubElement(
                        declarations,
                        "declaration",
                        type=_get_decl_attr(decl, "kind", "unknown"),
                        name=_get_decl_attr(decl, "name", "unnamed"),
                        lines=f"{start_line}-{end_line}",
                    )

            # Add security findings
            if hasattr(item, "security_issues") and item.security_issues:
                security = ET.SubElement(analysis, "security_findings")
                for issue in item.security_issues:
                    severity = _get_issue_attr(issue, "severity", "INFO")
                    # Handle enum with .value attribute
                    if hasattr(severity, "value"):
                        severity_str = str(severity.value)
                    else:
                        severity_str = str(severity)
                    ET.SubElement(
                        security,
                        "issue",
                        severity=severity_str,
                        line=str(_get_issue_attr(issue, "line_number", 0)),
                        rule=_get_issue_attr(issue, "rule_id", ""),
                    ).text = _get_issue_attr(issue, "description", "")

        # File content with CDATA preservation
        if hasattr(item, "diff_content") and item.diff_content:
            # For diff mode, include both diff and regular content
            diff_content_elem = ET.SubElement(file_entry, "diff_content")
            diff_content_elem.text = item.diff_content

        content_elem = ET.SubElement(file_entry, "file_content")
        content_elem.text = getattr(item, "content", "")

        # Add compression segments if applicable
        if config.enable_compression and hasattr(config, "_compressed_segments"):
            segments = CompressionHelper.extract_compressed_segments(
                config, getattr(item, "file_path", "")
            )
            if segments:
                file_entry.set("has_compression", "true")
                segs_elem = ET.SubElement(file_entry, "compression_segments")
                for seg in segments:
                    seg_elem = ET.SubElement(
                        segs_elem,
                        "segment",
                        type=seg.segment_type.value,
                        lines=f"{seg.start_line}-{seg.end_line}",
                    )
                    seg_elem.text = seg.content

    # Relationships section for understanding connections
    relationships = ET.SubElement(root, "file_relationships")
    relationships.text = "File dependency and import relationships would be analyzed here"

    # Convert to string with proper formatting
    try:
        rough_string = ET.tostring(root, "utf-8")
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

        # Add CDATA sections for content preservation
        xml_str = _add_cdata_sections_optimized(xml_str)
    except Exception:
        xml_str = ET.tostring(root, encoding="unicode")
        xml_str = _add_cdata_sections_optimized(xml_str)

    return xml_str


def _calculate_diff_statistics(items: list[WritableItem]) -> dict:
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


def _add_cdata_sections_optimized(xml_str: str) -> str:
    """Add CDATA sections to elements that need content preservation."""
    import html
    import re

    # Elements that should have CDATA-wrapped content
    cdata_elements = [
        "project_structure",
        "file_content",
        "diff_content",
        "processing_instructions",
        "content",
        "segment",
    ]

    for element_name in cdata_elements:
        pattern = f"<{element_name}>([^<]+)</{element_name}>"

        def replace_with_cdata(match, elem_name=element_name):
            content = match.group(1)
            if content.strip().startswith("<![CDATA["):
                return match.group(0)
            # Unescape XML entities before wrapping in CDATA since CDATA
            # preserves content literally (so &quot; would stay as &quot;)
            content = html.unescape(content)
            return f"<{elem_name}><![CDATA[{content}]]></{elem_name}>"

        xml_str = re.sub(pattern, replace_with_cdata, xml_str, flags=re.DOTALL)

    return xml_str
