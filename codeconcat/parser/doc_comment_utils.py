"""Shared utilities for cleaning and normalizing documentation comments.

This module provides reusable functions for extracting and cleaning documentation
comments from various programming languages. These utilities are used by tree-sitter
parsers to normalize docstrings, Javadoc, JSDoc, Doxygen, XML doc comments, and
other documentation formats into plain text.

Functions:
    clean_line_comments: Clean line-based documentation comments (e.g., //, #, #').
    clean_block_comments: Clean block-based documentation comments (e.g., /** */).
    clean_xml_doc_comments: Clean C# XML documentation comments.
    normalize_whitespace: Normalize whitespace in cleaned documentation.
"""

import re
from typing import List


def clean_line_comments(
    lines: List[str],
    prefix_pattern: str = r"^(///?|#+)",
    strip_whitespace: bool = True,
    join_lines: bool = True,
) -> str:
    """Clean line-based documentation comments.

    Used for Go (//), Rust (/// or //!), PHP (#), Julia (#=), R (#'), and similar
    languages that use line-based documentation comments.

    Args:
        lines: List of comment lines to clean.
        prefix_pattern: Regex pattern matching the comment prefix to remove.
        strip_whitespace: Whether to strip leading/trailing whitespace from each line.
        join_lines: Whether to join lines with spaces (True) or newlines (False).

    Returns:
        Cleaned documentation string.

    Examples:
        >>> clean_line_comments(["/// This is", "/// a doc comment"], r"^///")
        'This is a doc comment'

        >>> clean_line_comments(["#' Roxygen comment", "#' Second line"], r"^#'")
        'Roxygen comment Second line'
    """
    if not lines:
        return ""

    prefix_re = re.compile(prefix_pattern)
    cleaned_lines: List[str] = []

    for line in lines:
        # Remove comment prefix
        cleaned = prefix_re.sub("", line, count=1)

        # Strip whitespace if requested
        if strip_whitespace:
            cleaned = cleaned.strip()

        # Only add non-empty lines
        if cleaned:
            cleaned_lines.append(cleaned)

    # Join lines with space or newline
    separator = " " if join_lines else "\n"
    result = separator.join(cleaned_lines)

    # Only normalize if we're joining lines and stripping whitespace
    return normalize_whitespace(result) if (join_lines and strip_whitespace) else result


def clean_block_comments(
    lines: List[str],
    start_pattern: str = r"^/\*\*",
    line_pattern: str = r"^\s*\*",
    end_pattern: str = r"\*/$",
    preserve_structure: bool = False,
) -> str:
    """Clean block-based documentation comments.

    Used for Java (/** */), C++ (/** */ or /*! */), JavaScript/TypeScript (/** */),
    and similar languages that use block-based documentation comments.

    Args:
        lines: List of comment lines to clean.
        start_pattern: Regex pattern matching the opening delimiter (e.g., /**).
        line_pattern: Regex pattern matching line prefixes to remove (e.g., *).
        end_pattern: Regex pattern matching the closing delimiter (e.g., */).
        preserve_structure: Whether to preserve line breaks (True) or join lines (False).

    Returns:
        Cleaned documentation string.

    Examples:
        >>> clean_block_comments(["/**", " * This is a", " * doc comment", " */"])
        'This is a doc comment'

        >>> clean_block_comments(["/*!", " * Doxygen comment", " */"], start_pattern=r"^/\\*!")
        'Doxygen comment'
    """
    if not lines:
        return ""

    start_re = re.compile(start_pattern)
    line_re = re.compile(line_pattern)
    end_re = re.compile(end_pattern)
    cleaned_lines: List[str] = []

    for i, line in enumerate(lines):
        cleaned = line

        # Remove opening delimiter from first line
        if i == 0:
            cleaned = start_re.sub("", cleaned, count=1)

        # Remove closing delimiter from last line
        if i == len(lines) - 1:
            cleaned = end_re.sub("", cleaned, count=1)

        # Remove line prefix (* or similar)
        cleaned = line_re.sub("", cleaned, count=1)

        # Strip whitespace
        cleaned = cleaned.strip()

        # Only add non-empty lines
        if cleaned:
            cleaned_lines.append(cleaned)

    # Join lines based on structure preference
    if preserve_structure:
        return "\n".join(cleaned_lines)
    else:
        result = " ".join(cleaned_lines)
        return normalize_whitespace(result)


def clean_xml_doc_comments(xml_content: str, extract_tags: bool = True) -> str:
    """Clean C# XML documentation comments.

    Parses C# XML doc comments and extracts meaningful text content. Uses defusedxml
    when available for security, falls back to standard xml.etree.ElementTree.

    Args:
        xml_content: Raw XML documentation string.
        extract_tags: Whether to extract and format specific tags like <summary>,
                     <param>, <returns> (True) or just return all text (False).

    Returns:
        Cleaned documentation string.

    Examples:
        >>> xml = '<summary>This is a summary</summary>'
        >>> clean_xml_doc_comments(xml)
        'This is a summary'

        >>> xml = '<summary>Summary</summary><param name="x">Parameter</param>'
        >>> clean_xml_doc_comments(xml, extract_tags=True)
        'Summary\\nParam x: Parameter'
    """
    if not xml_content or not xml_content.strip():
        return ""

    # Try to use defusedxml for security (prevents XXE attacks)
    try:
        import defusedxml.ElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET

    try:
        # Wrap content in root element if not already wrapped
        if not xml_content.strip().startswith("<root"):
            xml_content = f"<root>{xml_content}</root>"

        root = ET.fromstring(xml_content)

        if not extract_tags:
            # Simple extraction - just get all text
            return normalize_whitespace(ET.tostring(root, encoding="unicode", method="text"))

        # Extract specific tags with formatting
        parts: List[str] = []

        # Extract summary
        summary = root.find("summary")
        if summary is not None and summary.text:
            parts.append(summary.text.strip())

        # Extract parameters
        for param in root.findall("param"):
            param_name = param.get("name", "")
            param_text = param.text.strip() if param.text else ""
            if param_text:
                parts.append(f"Param {param_name}: {param_text}")

        # Extract returns
        returns = root.find("returns")
        if returns is not None and returns.text:
            parts.append(f"Returns: {returns.text.strip()}")

        # Extract remarks
        remarks = root.find("remarks")
        if remarks is not None and remarks.text:
            parts.append(f"Remarks: {remarks.text.strip()}")

        # Extract exceptions
        for exception in root.findall("exception"):
            exc_type = exception.get("cref", "")
            exc_text = exception.text.strip() if exception.text else ""
            if exc_text:
                parts.append(f"Throws {exc_type}: {exc_text}")

        return "\n".join(parts) if parts else ""

    except Exception:
        # If XML parsing fails, return cleaned raw content
        # Remove XML-like tags with regex
        cleaned = re.sub(r"<[^>]+>", " ", xml_content)
        return normalize_whitespace(cleaned)


def normalize_whitespace(text: str, collapse_newlines: bool = True) -> str:
    """Normalize whitespace in documentation text.

    Removes excessive whitespace, collapses multiple spaces into one, and optionally
    collapses multiple newlines into one.

    Args:
        text: Text to normalize.
        collapse_newlines: Whether to collapse multiple newlines into one.

    Returns:
        Text with normalized whitespace.

    Examples:
        >>> normalize_whitespace("This  has   multiple    spaces")
        'This has multiple spaces'

        >>> normalize_whitespace("Line1\\n\\n\\nLine2", collapse_newlines=True)
        'Line1\\nLine2'
    """
    if not text:
        return ""

    # Collapse multiple spaces into one
    text = re.sub(r" +", " ", text)

    # Collapse multiple newlines into one if requested
    if collapse_newlines:
        text = re.sub(r"\n\n+", "\n", text)

    # Remove leading/trailing whitespace
    return text.strip()


def clean_jsdoc_tags(text: str) -> str:
    """Clean JSDoc/JavaDoc tags from documentation text.

    Removes JSDoc/JavaDoc tags like @param, @returns, @throws, etc. and formats
    them as readable text.

    Args:
        text: JSDoc text containing tags.

    Returns:
        Cleaned text with tags formatted as readable sentences.

    Examples:
        >>> clean_jsdoc_tags("@param {string} name - The name\\n@returns {boolean}")
        'Param name (string): The name\\nReturns: boolean'
    """
    if not text:
        return ""

    lines = text.split("\n")
    cleaned_lines: List[str] = []

    for line in lines:
        line = line.strip()

        # Handle @param tags
        param_match = re.match(r"@param\s+(?:\{([^}]+)\}\s+)?(\w+)\s*-?\s*(.*)", line)
        if param_match:
            param_type = param_match.group(1) or ""
            param_name = param_match.group(2)
            param_desc = param_match.group(3)
            if param_type:
                cleaned_lines.append(f"Param {param_name} ({param_type}): {param_desc}")
            else:
                cleaned_lines.append(f"Param {param_name}: {param_desc}")
            continue

        # Handle @returns/@return tags
        returns_match = re.match(r"@returns?\s+(?:\{([^}]+)\}\s*)?(.*)", line)
        if returns_match:
            return_type = returns_match.group(1) or ""
            return_desc = returns_match.group(2)
            if return_type and return_desc:
                cleaned_lines.append(f"Returns ({return_type}): {return_desc}")
            elif return_type:
                cleaned_lines.append(f"Returns: {return_type}")
            elif return_desc:
                cleaned_lines.append(f"Returns: {return_desc}")
            continue

        # Handle @throws/@exception tags
        throws_match = re.match(r"@(?:throws|exception)\s+(?:\{([^}]+)\}\s*)?(.*)", line)
        if throws_match:
            exc_type = throws_match.group(1) or ""
            exc_desc = throws_match.group(2)
            if exc_type and exc_desc:
                cleaned_lines.append(f"Throws {exc_type}: {exc_desc}")
            elif exc_type:
                cleaned_lines.append(f"Throws: {exc_type}")
            continue

        # Handle other common tags (remove @ prefix)
        tag_match = re.match(r"@(\w+)\s+(.*)", line)
        if tag_match:
            tag_name = tag_match.group(1).capitalize()
            tag_content = tag_match.group(2)
            cleaned_lines.append(f"{tag_name}: {tag_content}")
            continue

        # Keep non-tag lines as-is
        if line and not line.startswith("@"):
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)
