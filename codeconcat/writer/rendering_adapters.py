"""
rendering_adapters.py

This module provides adapters for rendering structured data into various output formats.
It decouples the data models from the presentation logic, enabling more flexibility
in how content is rendered.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    ContentSegment,
    ContentSegmentType,
    Declaration,
    ParsedDocData,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
)

logger = logging.getLogger(__name__)


class MarkdownRenderAdapter:
    """Adapter for rendering structured data to Markdown format."""

    @staticmethod
    def render_declarations(
        declarations: list[Declaration], _file_path: str, _config: CodeConCatConfig
    ) -> str:
        """Render a list of declarations as a markdown list."""
        if not declarations:
            return ""

        result = ["### Declarations\n"]

        # Create a function to recursively add declarations with proper indentation
        def add_declaration_with_children(decl: Declaration, indent: int = 0):
            """Add a formatted declaration string with children to a result list.
            Parameters:
                - decl (Declaration): The declaration object to be formatted and added, which includes attributes like kind, name, start_line, end_line, modifiers, and children.
                - indent (int, optional): The indentation level for formatting the output, default is 0.
            Returns:
                - None: The function modifies a global result list by appending a formatted string representation of the declaration and its children."""
            indent_str = "  " * indent
            kind_display = f"{decl.kind.capitalize()}"

            # Format the declaration line
            decl_line = f"{indent_str}- **{kind_display}**: `{decl.name}`"

            # Add line range
            decl_line += f" (lines {decl.start_line}-{decl.end_line})"

            # Add modifiers if present
            if decl.modifiers:
                mods = ", ".join(decl.modifiers)
                decl_line += f" [{mods}]"

            result.append(decl_line)

            # Process children with increased indentation
            for child in decl.children:
                add_declaration_with_children(child, indent + 1)

        # Process top-level declarations
        for decl in declarations:
            add_declaration_with_children(decl)

        return "\n".join(result)

    @staticmethod
    def render_imports(imports: list[str]) -> str:
        """Render a list of imports as a markdown list."""
        if not imports:
            return ""

        result = ["### Imports\n"]
        for imp in imports:
            result.append(f"- `{imp}`")
        return "\n".join(result)

    @staticmethod
    def render_security_issues(issues: list[SecurityIssue]) -> str:
        """Render security issues as a markdown section with severity-based formatting."""
        if not issues:
            return ""

        # Sort issues by severity (most severe first)
        sorted_issues = sorted(issues, key=lambda x: x.severity, reverse=True)

        result = ["### Security Issues\n"]
        result.append("| Severity | Rule | Line | Description |")
        result.append("|----------|------|------|-------------|")

        for issue in sorted_issues:
            # Format severity with color indicators
            if issue.severity == SecuritySeverity.CRITICAL:
                severity_display = "🔴 CRITICAL"
            elif issue.severity == SecuritySeverity.HIGH:
                severity_display = "🟠 HIGH"
            elif issue.severity == SecuritySeverity.MEDIUM:
                severity_display = "🟡 MEDIUM"
            elif issue.severity == SecuritySeverity.LOW:
                severity_display = "🟢 LOW"
            else:  # INFO
                severity_display = "ℹ️ INFO"

            result.append(
                f"| {severity_display} | {issue.rule_id} | {issue.line_number} | {issue.description} |"
            )

        return "\n".join(result)

    @staticmethod
    def render_token_stats(token_stats: TokenStats | None) -> str:
        """Render token statistics as a markdown section."""
        if not token_stats:
            return ""

        result = ["### Token Statistics\n"]
        result.append("| Model | Token Count |")
        result.append("|-------|-------------|")
        result.append(f"| GPT-4 | {token_stats.gpt4_tokens:,} |")
        result.append(f"| Claude | {token_stats.claude_tokens:,} |")

        return "\n".join(result)

    @staticmethod
    def render_file_content(
        content: str, language: str, config: CodeConCatConfig, file_path: str | None = None
    ) -> str:
        """Render file content as a markdown code block with appropriate language tag."""
        # Special case for empty content
        if not content:
            return "```\n// No content\n```"

        # Add line numbers if configured
        if config.show_line_numbers:
            # Split content by lines, add line numbers, and rejoin
            lines = content.split("\n")
            content_with_numbers = ""

            for i, line in enumerate(lines, 1):
                content_with_numbers += f"{i:4d} | {line}\n"

            content = content_with_numbers.rstrip("\n")

        # If compression is enabled and segments are provided in metadata,
        # handle compression styling for placeholder text
        if (
            config.enable_compression
            and hasattr(config, "_compressed_segments")
            and config._compressed_segments
        ):
            # Handle both formats: dictionary with file paths as keys or direct list of segments
            segments_to_use = None

            # Check if segments are stored as a dictionary with file path as key
            if (
                file_path is not None
                and isinstance(config._compressed_segments, dict)
                and file_path in config._compressed_segments
            ):
                segments_to_use = config._compressed_segments[file_path]
            # Check if segments are stored directly as a list (for tests)
            elif isinstance(config._compressed_segments, list):
                segments_to_use = config._compressed_segments

            if segments_to_use:
                return MarkdownRenderAdapter._render_compressed_content(segments_to_use, language)

        # Use language tag if available
        lang_tag = language if language and language != "unknown" else ""

        # Create the markdown code block
        return f"```{lang_tag}\n{content}\n```"

    @staticmethod
    def _render_compressed_content(segments: list[ContentSegment], language: str) -> str:
        """Render compressed content with special formatting for placeholders."""
        # Use language tag if available
        lang_tag = language if language and language != "unknown" else ""

        result = [f"```{lang_tag}"]

        for segment in segments:
            if segment.segment_type == ContentSegmentType.OMITTED:
                # Style the placeholder differently - ensure the placeholder is visible
                result.append(f"\n{segment.content}\n")
            else:
                # Regular code segment
                result.append(segment.content)

        result.append("```")
        return "\n".join(result)

    @staticmethod
    def render_annotated_file(file_data: AnnotatedFileData, config: CodeConCatConfig) -> list[str]:
        """Render a full annotated file as a list of markdown chunks."""
        result = []

        # File header with path
        result.append(f"## File: {file_data.file_path}\n")

        # Add summary if present and configured
        if file_data.summary and config.include_file_summary:
            result.append(f"### Summary\n{file_data.summary}\n")

        # Add tags if present
        if file_data.tags:
            tag_str = ", ".join([f"`{tag}`" for tag in file_data.tags])
            result.append(f"**Tags**: {tag_str}\n")

        # Add structured data sections if configured
        if config.include_declarations_in_summary and not config.disable_symbols:
            declarations_md = MarkdownRenderAdapter.render_declarations(
                file_data.declarations, file_data.file_path, config
            )
            if declarations_md:
                result.append(declarations_md + "\n")

        if config.include_imports_in_summary:
            imports_md = MarkdownRenderAdapter.render_imports(file_data.imports)
            if imports_md:
                result.append(imports_md + "\n")

        if (
            config.include_security_in_summary
            and file_data.security_issues
            and not config.mask_output_content
        ):
            security_md = MarkdownRenderAdapter.render_security_issues(file_data.security_issues)
            if security_md:
                result.append(security_md + "\n")

        if (
            config.include_tokens_in_summary
            and file_data.token_stats
            and config.enable_token_counting
        ):
            tokens_md = MarkdownRenderAdapter.render_token_stats(file_data.token_stats)
            if tokens_md:
                result.append(tokens_md + "\n")

        # Add the file content
        content_to_render = (
            file_data.annotated_content if file_data.annotated_content else file_data.content
        )
        content_md = MarkdownRenderAdapter.render_file_content(
            content_to_render, file_data.language, config, file_data.file_path
        )
        result.append(content_md)

        return result

    @staticmethod
    def render_doc_file(doc_data: ParsedDocData, _config: CodeConCatConfig) -> list[str]:
        """Render a documentation file as a list of markdown chunks."""
        result = []

        # Doc file header
        result.append(f"## Documentation: {doc_data.file_path}\n")

        # Add summary if present
        if doc_data.summary:
            result.append(f"### Summary\n{doc_data.summary}\n")

        # Add tags if present
        if doc_data.tags:
            tag_str = ", ".join([f"`{tag}`" for tag in doc_data.tags])
            result.append(f"**Tags**: {tag_str}\n")

        # Add the doc content
        result.append(doc_data.content)

        return result


class JsonRenderAdapter:
    """Adapter for rendering structured data to JSON format."""

    @staticmethod
    def declaration_to_dict(decl: Declaration) -> dict[str, Any]:
        """Convert a Declaration object to a dictionary for JSON serialization."""
        return {
            "kind": decl.kind,
            "name": decl.name,
            "start_line": decl.start_line,
            "end_line": decl.end_line,
            "modifiers": list(decl.modifiers),
            "docstring": decl.docstring,
            "children": [JsonRenderAdapter.declaration_to_dict(child) for child in decl.children],
        }

    @staticmethod
    def security_issue_to_dict(issue: SecurityIssue) -> dict[str, Any]:
        """Convert a SecurityIssue object to a dictionary for JSON serialization."""
        return {
            "rule_id": issue.rule_id,
            "description": issue.description,
            "line_number": issue.line_number,
            "severity": issue.severity.value,
            "context": issue.context,
        }

    @staticmethod
    def token_stats_to_dict(token_stats: TokenStats | None) -> dict[str, Any] | None:
        """Convert a TokenStats object to a dictionary for JSON serialization."""
        if not token_stats:
            return None

        # Convert TokenStats to a dict, handling all token models
        return {
            "gpt4_tokens": token_stats.gpt4_tokens,
            "claude_tokens": token_stats.claude_tokens,
        }

    @staticmethod
    def segment_to_dict(segment: ContentSegment) -> dict[str, Any]:
        """Convert a ContentSegment to a dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "type": segment.segment_type.value,
            "content": segment.content,
            "start_line": segment.start_line,
            "end_line": segment.end_line,
        }

        # Include metadata if present
        if segment.metadata:
            # Filter out original_content from JSON for brevity if present
            metadata = {k: v for k, v in segment.metadata.items() if k != "original_content"}
            result["metadata"] = metadata

        return result

    @staticmethod
    def annotated_file_to_dict(
        file_data: AnnotatedFileData, config: CodeConCatConfig
    ) -> dict[str, Any]:
        """Convert an AnnotatedFileData object to a dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "file_path": file_data.file_path,
            "language": file_data.language or "unknown",
        }

        if file_data.summary and config.include_file_summary:
            result["summary"] = file_data.summary

        if file_data.tags:
            result["tags"] = file_data.tags

        # Include content data based on config
        if not config.disable_symbols and file_data.declarations:
            result["declarations"] = [
                JsonRenderAdapter.declaration_to_dict(d) for d in file_data.declarations
            ]

        if file_data.imports:
            result["imports"] = file_data.imports

        if file_data.security_issues and not config.mask_output_content:
            result["security_issues"] = [
                JsonRenderAdapter.security_issue_to_dict(i) for i in file_data.security_issues
            ]

        if config.enable_token_counting and file_data.token_stats:
            result["token_stats"] = JsonRenderAdapter.token_stats_to_dict(file_data.token_stats)

        # Handle compression if enabled
        if (
            config.enable_compression
            and hasattr(config, "_compressed_segments")
            and config._compressed_segments
            and file_data.file_path in config._compressed_segments
        ):
            file_segments = config._compressed_segments[file_data.file_path]
            result["compression_applied"] = True
            result["segments"] = [JsonRenderAdapter.segment_to_dict(s) for s in file_segments]

            # Count lines for each segment type
            result["segment_stats"] = {"total_lines": 0, "kept_lines": 0, "omitted_lines": 0}
            segments_content = []
            for segment in file_segments:
                segments_content.append(segment.content)
            result["content"] = "\n".join(segments_content)
        else:
            # Include actual content (not compressed)
            content_to_use = (
                file_data.annotated_content if file_data.annotated_content else file_data.content
            )
            result["content"] = content_to_use or ""
            result["compression_applied"] = False

        return result

    @staticmethod
    def doc_file_to_dict(doc_data: ParsedDocData, _config: CodeConCatConfig) -> dict[str, Any]:
        """Convert a ParsedDocData object to a dictionary for JSON serialization."""
        return {
            "file_path": doc_data.file_path,
            "content": doc_data.content,
            "doc_type": doc_data.doc_type,
            "summary": doc_data.summary,
            "tags": doc_data.tags,
        }


class XmlRenderAdapter:
    """Adapter for rendering structured data to XML format."""

    @staticmethod
    def add_declaration_to_element(parent: ET.Element, decl: Declaration):
        """Add a Declaration object as an XML element to a parent element."""
        decl_elem = ET.SubElement(parent, "declaration")
        decl_elem.set("kind", decl.kind)
        decl_elem.set("name", decl.name)
        decl_elem.set("start_line", str(decl.start_line))
        decl_elem.set("end_line", str(decl.end_line))

        # Add modifiers
        if decl.modifiers:
            mods_elem = ET.SubElement(decl_elem, "modifiers")
            for mod in decl.modifiers:
                mod_elem = ET.SubElement(mods_elem, "modifier")
                mod_elem.text = mod

        # Add docstring
        if decl.docstring:
            doc_elem = ET.SubElement(decl_elem, "docstring")
            doc_elem.text = decl.docstring

        # Add children recursively
        if decl.children:
            children_elem = ET.SubElement(decl_elem, "children")
            for child in decl.children:
                XmlRenderAdapter.add_declaration_to_element(children_elem, child)

    @staticmethod
    def add_security_issue_to_element(parent: ET.Element, issue: SecurityIssue):
        """Add a SecurityIssue object as an XML element to a parent element."""
        issue_elem = ET.SubElement(parent, "security_issue")
        issue_elem.set("rule_id", issue.rule_id)
        issue_elem.set("line_number", str(issue.line_number))
        issue_elem.set("severity", issue.severity.value)

        # Add description
        desc_elem = ET.SubElement(issue_elem, "description")
        desc_elem.text = issue.description

        # Add context if present
        if issue.context:
            ctx_elem = ET.SubElement(issue_elem, "context")
            ctx_elem.text = issue.context

    @staticmethod
    def add_token_stats_to_element(parent: ET.Element, token_stats: TokenStats):
        """Add a TokenStats object as an XML element to a parent element."""
        stats_elem = ET.SubElement(parent, "token_stats")

        gpt4_elem = ET.SubElement(stats_elem, "model")
        gpt4_elem.set("name", "gpt4")
        gpt4_elem.set("tokens", str(token_stats.gpt4_tokens))

        claude_elem = ET.SubElement(stats_elem, "model")
        claude_elem.set("name", "claude")
        claude_elem.set("tokens", str(token_stats.claude_tokens))

    @staticmethod
    def create_annotated_file_element(
        file_data: AnnotatedFileData, config: CodeConCatConfig
    ) -> ET.Element:
        """Create an XML element representing an AnnotatedFileData object."""
        file_element = ET.Element("file")
        file_element.set("path", file_data.file_path)
        file_element.set("language", file_data.language or "unknown")

        # Add summary if present and configured
        if file_data.summary and config.include_file_summary:
            summary_elem = ET.SubElement(file_element, "summary")
            summary_elem.text = file_data.summary

        # Add tags if present
        if file_data.tags:
            tags_elem = ET.SubElement(file_element, "tags")
            for tag in file_data.tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = tag

        # Add declarations if present and configured
        if not config.disable_symbols and file_data.declarations:
            declarations_elem = ET.SubElement(file_element, "declarations")
            for decl in file_data.declarations:
                XmlRenderAdapter.add_declaration_to_element(declarations_elem, decl)

        # Add imports if present
        if file_data.imports:
            imports_elem = ET.SubElement(file_element, "imports")
            for imp in file_data.imports:
                import_elem = ET.SubElement(imports_elem, "import")
                import_elem.text = imp

        # Add security issues if present and not masked
        if file_data.security_issues and not config.mask_output_content:
            security_elem = ET.SubElement(file_element, "security_issues")
            for issue in file_data.security_issues:
                XmlRenderAdapter.add_security_issue_to_element(security_elem, issue)

        # Add token stats if present and configured
        if config.enable_token_counting and file_data.token_stats:
            token_stats_elem = ET.SubElement(file_element, "token_stats")
            XmlRenderAdapter.add_token_stats_to_element(token_stats_elem, file_data.token_stats)

        # Handle compressed content if enabled
        if (
            config.enable_compression
            and hasattr(config, "_compressed_segments")
            and config._compressed_segments
            and file_data.file_path in config._compressed_segments
        ):
            file_segments = config._compressed_segments[file_data.file_path]
            file_element.set("compression_applied", "true")

            # Create an element for each segment
            segments_element = ET.SubElement(file_element, "segments")
            for segment in file_segments:
                segment_elem = ET.SubElement(segments_element, "segment")
                segment_elem.set("type", segment.segment_type.value)
                segment_elem.set("start_line", str(segment.start_line))
                segment_elem.set("end_line", str(segment.end_line))

                # Add content
                content_elem = ET.SubElement(segment_elem, "content")
                content_elem.text = segment.content

                # Add metadata if present
                if segment.metadata:
                    metadata_elem = ET.SubElement(segment_elem, "metadata")
                    for key, value in segment.metadata.items():
                        if key != "original_content" and isinstance(value, (str, int, float, bool)):
                            meta_item = ET.SubElement(metadata_elem, "item", {"key": key})
                            meta_item.text = str(value)

            # Also include the combined content
            content_elem = ET.SubElement(file_element, "content")
            content_elem.text = "\n".join(s.content for s in file_segments)
        else:
            # Add the file content without compression
            file_element.set("compression_applied", "false")
            content_to_use = (
                file_data.annotated_content if file_data.annotated_content else file_data.content
            )
            content_elem = ET.SubElement(file_element, "content")
            content_elem.text = content_to_use or ""

        return file_element

    @staticmethod
    def create_doc_file_element(doc_data: ParsedDocData, _config: CodeConCatConfig) -> ET.Element:
        """Create an XML element representing a ParsedDocData object."""
        doc_elem = ET.Element("doc")
        doc_elem.set("path", doc_data.file_path)
        doc_elem.set("type", doc_data.doc_type)

        # Add summary if present
        if doc_data.summary:
            summary_elem = ET.SubElement(doc_elem, "summary")
            summary_elem.text = doc_data.summary

        # Add tags if present
        if doc_data.tags:
            tags_elem = ET.SubElement(doc_elem, "tags")
            for tag in doc_data.tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = tag

        # Add content
        content_elem = ET.SubElement(doc_elem, "content")
        content_elem.text = doc_data.content

        return doc_elem


class TextRenderAdapter:
    """Adapter for rendering structured data to plain text format."""

    @staticmethod
    def render_declarations(declarations: list[Declaration]) -> list[str]:
        """Render a list of declarations as plain text lines."""
        if not declarations:
            return []

        result = ["=== DECLARATIONS ==="]

        def add_declaration_with_children(decl: Declaration, indent: int = 0):
            """Add a declaration and its children to a result list with indentation and formatting.
            Parameters:
                - decl (Declaration): The declaration object to add, containing information such as kind, name, line range, and modifiers.
                - indent (int): The indentation level for formatting the declaration and its children.
            Returns:
                - None: This function appends formatted declaration lines to a global result list and does not return a value."""
            indent_str = "  " * indent
            kind_display = f"{decl.kind.capitalize()}"

            # Format the declaration line
            decl_line = f"{indent_str}{kind_display}: {decl.name}"

            # Add line range
            decl_line += f" (lines {decl.start_line}-{decl.end_line})"

            # Add modifiers if present
            if decl.modifiers:
                mods = ", ".join(decl.modifiers)
                decl_line += f" [{mods}]"

            result.append(decl_line)

            # Process children with increased indentation
            for child in decl.children:
                add_declaration_with_children(child, indent + 1)

        # Process top-level declarations
        for decl in declarations:
            add_declaration_with_children(decl)

        return result

    @staticmethod
    def render_imports(imports: list[str]) -> list[str]:
        """Render a list of imports as plain text lines."""
        if not imports:
            return []

        result = ["=== IMPORTS ==="]
        for imp in imports:
            result.append(f"- {imp}")
        return result

    @staticmethod
    def render_security_issues(issues: list[SecurityIssue]) -> list[str]:
        """Render security issues as plain text lines."""
        if not issues:
            return []

        # Sort issues by severity (most severe first)
        sorted_issues = sorted(issues, key=lambda x: x.severity, reverse=True)

        result = ["=== SECURITY ISSUES ==="]

        for issue in sorted_issues:
            result.append(
                f"[{issue.severity.value}] {issue.rule_id} - Line {issue.line_number}: {issue.description}"
            )

        return result

    @staticmethod
    def render_token_stats(token_stats: TokenStats | None) -> list[str]:
        """Render token statistics as plain text lines."""
        if not token_stats:
            return []

        result = ["=== TOKEN STATISTICS ==="]
        result.append(f"GPT-4: {token_stats.gpt4_tokens:,}")
        result.append(f"Claude: {token_stats.claude_tokens:,}")

        return result

    @staticmethod
    def render_file_content(content: str, config: CodeConCatConfig) -> list[str]:
        """Render file content as plain text lines."""
        # Add line numbers if configured
        if config.show_line_numbers:
            # Split content by lines, add line numbers
            lines = content.split("\n")
            result = []

            for i, line in enumerate(lines, 1):
                result.append(f"{i:4d} | {line}")

            return result
        else:
            return content.split("\n")

    @staticmethod
    def render_annotated_file(file_data: AnnotatedFileData, config: CodeConCatConfig) -> list[str]:
        """Render a full annotated file as a list of plain text lines."""
        result = []

        # File header with path
        result.append("")
        result.append("=" * 80)
        result.append(f"FILE: {file_data.file_path}")
        result.append("=" * 80)

        # Add summary if present and configured
        if file_data.summary and config.include_file_summary:
            result.append("")
            result.append("=== SUMMARY ===")
            result.extend(file_data.summary.split("\n"))

        # Add tags if present
        if file_data.tags:
            result.append("")
            result.append("=== TAGS ===")
            result.append(", ".join(file_data.tags))

        # Add structured data sections if configured
        if config.include_declarations_in_summary and not config.disable_symbols:
            result.append("")
            result.extend(TextRenderAdapter.render_declarations(file_data.declarations))

        if config.include_imports_in_summary:
            result.append("")
            result.extend(TextRenderAdapter.render_imports(file_data.imports))

        if (
            config.include_security_in_summary
            and file_data.security_issues
            and not config.mask_output_content
        ):
            result.append("")
            result.extend(TextRenderAdapter.render_security_issues(file_data.security_issues))

        if (
            config.include_tokens_in_summary
            and file_data.token_stats
            and config.enable_token_counting
        ):
            result.append("")
            result.extend(TextRenderAdapter.render_token_stats(file_data.token_stats))

        # Add the file content
        result.append("")
        result.append("=== CONTENT ===")
        content_to_render = (
            file_data.annotated_content if file_data.annotated_content else file_data.content
        )
        result.extend(TextRenderAdapter.render_file_content(content_to_render, config))

        return result

    @staticmethod
    def render_doc_file(doc_data: ParsedDocData, _config: CodeConCatConfig) -> list[str]:
        """Render a documentation file as a list of plain text lines."""
        result = []

        # Doc file header
        result.append("")
        result.append("=" * 80)
        result.append(f"DOCUMENTATION: {doc_data.file_path}")
        result.append("=" * 80)

        # Add summary if present
        if doc_data.summary:
            result.append("")
            result.append("=== SUMMARY ===")
            result.extend(doc_data.summary.split("\n"))

        # Add tags if present
        if doc_data.tags:
            result.append("")
            result.append("=== TAGS ===")
            result.append(", ".join(doc_data.tags))

        # Add the doc content
        result.append("")
        result.append("=== CONTENT ===")
        result.extend(doc_data.content.split("\n"))

        return result
