# file: codeconcat/parser/language_parsers/enhanced_csharp_parser.py

"""
Enhanced C# parser for CodeConcat.

This module provides an improved C# parser using the EnhancedCFamilyParser
with C#-specific patterns and functionality.
"""

import logging
import re
from typing import Dict, List, Optional

from codeconcat.parser.language_parsers.enhanced_c_family_parser import EnhancedCFamilyParser
from codeconcat.parser.language_parsers.pattern_library import (
    C_FAMILY_MODIFIERS,
)

logger = logging.getLogger(__name__)


class EnhancedCSharpParser(EnhancedCFamilyParser):
    """C# language parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced C# parser."""
        super().__init__()
        self.language = "csharp"
        self._setup_csharp_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for C#."""
        super()._setup_standard_patterns()

        # C# specific comment patterns
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Initialize recognized C# modifiers
        self.modifiers = set(
            C_FAMILY_MODIFIERS
            + [
                "async",
                "unsafe",
                "partial",
                "readonly",
                "internal",
                "event",
                "delegate",
                "ref",
                "out",
                "in",
                "global",
                "new",
                "where",
            ]
        )

    def _setup_csharp_patterns(self):
        """Setup C#-specific patterns."""
        # Start with C-family patterns
        self._setup_c_family_patterns()

        # Enhance with C#-specific patterns
        self.patterns["interface"] = re.compile(
            r"^\s*(?:(?:public|private|protected|internal|static|abstract|sealed|new|partial)\s+)*"
            r"interface\s+(?P<name>[\w<>]+)(?:\s*:\s*[\w\s,<>.]+)?\s*\{?",
            re.MULTILINE,
        )

        self.patterns["enum"] = re.compile(
            r"^\s*(?:(?:public|private|protected|internal)\s+)*"
            r"enum\s+(?P<name>\w+)(?:\s*:\s*\w+)?\s*\{?",
            re.MULTILINE,
        )

        self.patterns["property"] = re.compile(
            r"^\s*(?:(?:public|private|protected|internal|static|virtual|override|abstract|sealed|new|readonly)\s+)*"
            r"(?P<type>[\w<>\[\].]+)\s+(?P<name>\w+)\s*"
            r"\{\s*(?:get;|set;)",
            re.MULTILINE,
        )

        self.patterns["using"] = re.compile(
            r"^\s*using\s+(?:static\s+)?(?P<name>[\w.]+)(?:\s*=\s*[\w.]+)?;", re.MULTILINE
        )

    def _process_imports(self, line: str, imports: List[str]) -> bool:
        """
        Process C# using statements and add them to the imports list.

        Args:
            line: Line of code to process.
            imports: List to add imports to.

        Returns:
            True if line was a using statement, False otherwise.
        """
        if line.startswith("using ") and ";" in line:
            match = self.patterns["using"].match(line)
            if match:
                import_name = match.group("name")
                if import_name and import_name not in imports:
                    imports.append(import_name)
                return True
        return False

    def extract_docstring(self, lines: List[str], start: int, end: int) -> Optional[str]:
        """
        Extract C# docstring from lines, with special handling for XML comments.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index.

        Returns:
            Extracted docstring if found, None otherwise.
        """
        # First check for XML comments (///)
        xml_comment_lines = []
        i = start

        # Look for XML comments before the current position
        prev_i = start - 1
        while prev_i >= 0:
            prev_line = lines[prev_i].strip()
            if prev_line.startswith("///"):
                xml_comment_lines.insert(0, prev_line[3:].strip())
                prev_i -= 1
            else:
                break

        # If XML comments were found, return them
        if xml_comment_lines:
            return "\n".join(xml_comment_lines)

        # Otherwise, try standard C-family comment extraction
        return super().extract_docstring(lines, start, end)

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        capabilities = super().get_capabilities()
        capabilities.update(
            {
                "can_parse_imports": True,
                "can_parse_interfaces": True,
                "can_parse_enums": True,
                "can_parse_properties": True,
            }
        )
        return capabilities
