"""
Unified documentation extraction for all parsers in the CodeConCat project.

This module provides consistent docstring extraction across all parser
implementations, handling various documentation formats and languages
uniformly.
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DocstringStyle(Enum):
    """Documentation comment styles across languages."""

    PYTHON_TRIPLE = "python_triple"  # """docstring"""
    PYTHON_SINGLE = "python_single"  # # docstring
    JAVADOC = "javadoc"  # /** docstring */
    JAVADOC_SINGLE = "javadoc_single"  # /** docstring */
    JSDOC = "jsdoc"  # /** docstring */
    JSDOC_SINGLE = "jsdoc_single"  # // docstring
    GO_DOC = "go_doc"  # /* docstring */
    GO_DOC_SINGLE = "go_doc_single"  # // docstring
    RUST_DOC = "rust_doc"  # /// docstring
    RUST_DOC_INNER = "rust_doc_inner"  # //! docstring
    RUST_BLOCK = "rust_block"  # /* docstring */
    CSHARP_DOC = "csharp_doc"  # /// docstring
    CSHARP_DOC_SINGLE = "csharp_doc_single"  # // docstring
    CPP_DOC = "cpp_doc"  # /// docstring
    CPP_DOC_SINGLE = "cpp_doc_single"  # // docstring
    RUBY_DOC = "ruby_doc"  # =begin docstring
    RUBY_SINGLE = "ruby_single"  # # docstring
    SWIFT_DOC = "swift_doc"  # /** docstring */
    SWIFT_DOC_SINGLE = "swift_doc_single"  # // docstring
    KOTLIN_DOC = "kotlin_doc"  # /** docstring */
    KOTLIN_DOC_SINGLE = "kotlin_doc_single"  # // docstring
    DART_DOC = "dart_doc"  # /** docstring */
    DART_DOC_SINGLE = "dart_doc_single"  # // docstring
    UNKNOWN = "unknown"


class DocstringExtractor:
    """
    Unified docstring extraction across all programming languages.

    This class provides consistent extraction of documentation strings
    from various comment formats and languages.
    """

    # Language-specific docstring patterns
    LANGUAGE_PATTERNS: Dict[str, List[Tuple[DocstringStyle, re.Pattern]]] = {
        "python": [
            (DocstringStyle.PYTHON_TRIPLE, re.compile(r'"""(.*?)"""', re.DOTALL)),
            (DocstringStyle.PYTHON_TRIPLE, re.compile(r"'''(.*?)'''", re.DOTALL)),
            (DocstringStyle.PYTHON_SINGLE, re.compile(r"#\s*(.+)$", re.MULTILINE)),
        ],
        "javascript": [
            (DocstringStyle.JSDOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.JSDOC_SINGLE, re.compile(r"//\s*\*(.+)$", re.MULTILINE)),
            (DocstringStyle.JSDOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
        "typescript": [
            (DocstringStyle.JSDOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.JSDOC_SINGLE, re.compile(r"//\s*\*(.+)$", re.MULTILINE)),
            (DocstringStyle.JSDOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
        "java": [
            (DocstringStyle.JAVADOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.JAVADOC_SINGLE, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
        ],
        "c": [
            (DocstringStyle.CPP_DOC, re.compile(r"///\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.CPP_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.CPP_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
        ],
        "cpp": [
            (DocstringStyle.CPP_DOC, re.compile(r"///\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.CPP_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.CPP_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
        ],
        "csharp": [
            (DocstringStyle.CSHARP_DOC, re.compile(r"///\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.CSHARP_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.CSHARP_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
        ],
        "rust": [
            (DocstringStyle.RUST_DOC, re.compile(r"///\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.RUST_DOC_INNER, re.compile(r"//!\s*(.+)$", re.MULTILINE)),
            (DocstringStyle.RUST_BLOCK, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.RUST_BLOCK, re.compile(r"/\*(.*?)\*/", re.DOTALL)),
        ],
        "go": [
            (DocstringStyle.GO_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.GO_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
        "php": [
            (DocstringStyle.JAVADOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.JAVADOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
        "ruby": [
            (DocstringStyle.RUBY_DOC, re.compile(r"=begin\s*(.*?)\s*=end", re.DOTALL)),
            (DocstringStyle.RUBY_SINGLE, re.compile(r"#\s*(.+)$", re.MULTILINE)),
        ],
        "swift": [
            (DocstringStyle.SWIFT_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.SWIFT_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
        "kotlin": [
            (DocstringStyle.KOTLIN_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.KOTLIN_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
        "dart": [
            (DocstringStyle.DART_DOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
            (DocstringStyle.DART_DOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        ],
    }

    # Fallback patterns for unknown languages
    FALLBACK_PATTERNS: List[Tuple[DocstringStyle, re.Pattern]] = [
        (DocstringStyle.PYTHON_TRIPLE, re.compile(r'"""(.*?)"""', re.DOTALL)),
        (DocstringStyle.PYTHON_TRIPLE, re.compile(r"'''(.*?)'''", re.DOTALL)),
        (DocstringStyle.JAVADOC, re.compile(r"/\*\*(.*?)\*/", re.DOTALL)),
        (DocstringStyle.RUST_DOC, re.compile(r"///\s*(.+)$", re.MULTILINE)),
        (DocstringStyle.RUST_DOC_INNER, re.compile(r"//!\s*(.+)$", re.MULTILINE)),
        (DocstringStyle.JSDOC_SINGLE, re.compile(r"//\s*(.+)$", re.MULTILINE)),
        (DocstringStyle.PYTHON_SINGLE, re.compile(r"#\s*(.+)$", re.MULTILINE)),
    ]

    def __init__(self, language: str):
        """
        Initialize the docstring extractor for a specific language.

        Args:
            language: The programming language (e.g., 'python', 'javascript')
        """
        self.language = language.lower()
        self.patterns = self.LANGUAGE_PATTERNS.get(self.language, self.FALLBACK_PATTERNS)

    def extract_docstring(
        self, content: str, start_line: int, end_line: int, declaration_name: Optional[str] = None
    ) -> str:
        """
        Extract docstring for a declaration from the given content.

        Args:
            content: The full source content
            start_line: Starting line number of the declaration (1-based)
            end_line: Ending line number of the declaration (1-based)
            declaration_name: Name of the declaration (for better matching)

        Returns:
            Extracted docstring or empty string if not found
        """
        lines = content.split("\n")

        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)

        # Look for docstring before the declaration
        docstring = self._extract_preceding_docstring(lines, start_idx, declaration_name)

        # If not found, look for docstring inside the declaration (for Python functions)
        if not docstring:
            docstring = self._extract_internal_docstring(lines, start_idx, end_idx)

        # If still not found, look for docstring after the declaration (for some languages)
        if not docstring:
            docstring = self._extract_following_docstring(lines, start_idx, end_idx)

        return self._clean_docstring(docstring)

    def extract_all_docstrings(self, content: str) -> List[Tuple[int, int, str]]:
        """
        Extract all docstrings from the content.

        Args:
            content: The source content

        Returns:
            List of tuples (start_line, end_line, docstring)
        """
        docstrings = []

        for _doc_style, pattern in self.patterns:
            for match in pattern.finditer(content):
                # Calculate line numbers
                start_pos = match.start()
                end_pos = match.end()

                start_line = content[:start_pos].count("\n") + 1
                end_line = content[:end_pos].count("\n") + 1

                docstring = self._clean_docstring(
                    match.group(1) if match.groups() else match.group(0)
                )
                docstrings.append((start_line, end_line, docstring))

        return docstrings

    def _extract_preceding_docstring(
        self, lines: List[str], start_idx: int, _declaration_name: Optional[str] = None
    ) -> str:
        """
        Extract docstring that precedes a declaration.

        Args:
            lines: List of source lines
            start_idx: Starting index of the declaration
            declaration_name: Name of the declaration

        Returns:
            Extracted docstring or empty string
        """
        # Look backwards from the declaration start
        search_lines: List[str] = []
        search_start = start_idx - 1

        # Collect lines before the declaration
        for i in range(search_start, max(-1, search_start - 20), -1):
            line = lines[i].strip()

            # Stop if we hit another declaration or empty line without docstring
            if line and not self._is_docstring_line(line) and not line.startswith((" ", "\t")):
                break

            search_lines.insert(0, lines[i])

        search_text = "\n".join(search_lines)

        # Try to match patterns
        for _doc_style, pattern in self.patterns:
            for match in pattern.finditer(search_text):
                docstring = match.group(1) if match.groups() else match.group(0)
                if docstring.strip():
                    return docstring

        return ""

    def _extract_following_docstring(self, lines: List[str], _start_idx: int, end_idx: int) -> str:
        """
        Extract docstring that follows a declaration (for some languages).

        Args:
            lines: List of source lines
            start_idx: Starting index of the declaration
            end_idx: Ending index of the declaration

        Returns:
            Extracted docstring or empty string
        """
        # Look for docstring immediately after the declaration
        if end_idx >= len(lines):
            return ""

        # Check a few lines after the declaration
        search_lines = []
        for i in range(end_idx, min(len(lines), end_idx + 10)):
            line = lines[i]
            search_lines.append(line)

            # Stop if we hit non-docstring content
            if line.strip() and not self._is_docstring_line(line.strip()):
                break

        search_text = "\n".join(search_lines)

        # Try to match patterns
        for _doc_style, pattern in self.patterns:
            for match in pattern.finditer(search_text):
                docstring = match.group(1) if match.groups() else match.group(0)
                if docstring.strip():
                    return docstring

        return ""

    def _extract_internal_docstring(self, lines: List[str], start_idx: int, end_idx: int) -> str:
        """
        Extract docstring that is inside a declaration (e.g., Python function docstrings).

        Args:
            lines: List of source lines
            start_idx: Starting index of the declaration
            end_idx: Ending index of the declaration

        Returns:
            Extracted docstring or empty string
        """
        # Look for docstring inside the declaration body
        if start_idx >= len(lines) or end_idx > len(lines):
            return ""

        # Check lines within the declaration
        search_lines = []
        for i in range(start_idx, min(len(lines), end_idx)):
            line = lines[i]
            search_lines.append(line)

        search_text = "\n".join(search_lines)

        # Try to match patterns
        for _doc_style, pattern in self.patterns:
            for match in pattern.finditer(search_text):
                docstring = match.group(1) if match.groups() else match.group(0)
                if docstring.strip():
                    return docstring

        return ""

    def _is_docstring_line(self, line: str) -> bool:
        """
        Check if a line is part of a docstring.

        Args:
            line: The line to check

        Returns:
            True if the line is part of a docstring
        """
        docstring_prefixes = {'"""', "'''", "/**", "///", "//!", "/*", "//", "#", "*"}

        line_stripped = line.strip()
        return any(line_stripped.startswith(prefix) for prefix in docstring_prefixes)

    def _clean_docstring(self, docstring: str) -> str:
        """
        Clean and normalize a docstring.

        Args:
            docstring: The raw docstring

        Returns:
            Cleaned docstring
        """
        if not docstring:
            return ""

        # Remove common comment markers
        lines = docstring.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove leading comment markers and whitespace
            line = re.sub(r"^\s*(/\*\*|/\*|\*|///|//!|//|#)\s?", "", line)
            line = re.sub(r"\s*\*/$", "", line)  # Remove closing */
            cleaned_lines.append(line)

        # Join and clean up
        cleaned = "\n".join(cleaned_lines)

        # Remove excessive whitespace
        cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)  # Multiple newlines
        cleaned = re.sub(r"[ \t]+", " ", cleaned)  # Multiple spaces/tabs

        return cleaned.strip()


def create_docstring_extractor(language: str) -> DocstringExtractor:
    """
    Create a docstring extractor for a specific language.

    Args:
        language: The programming language

    Returns:
        Configured DocstringExtractor instance
    """
    return DocstringExtractor(language)


def extract_docstring(
    content: str,
    language: str,
    start_line: int,
    end_line: int,
    declaration_name: Optional[str] = None,
) -> str:
    """
    Convenience function to extract a docstring.

    Args:
        content: The source content
        language: The programming language
        start_line: Starting line number of the declaration
        end_line: Ending line number of the declaration
        declaration_name: Name of the declaration

    Returns:
        Extracted docstring or empty string
    """
    extractor = create_docstring_extractor(language)
    return extractor.extract_docstring(content, start_line, end_line, declaration_name)
