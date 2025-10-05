"""
Enhanced base parser implementations for the CodeConCat project.

This module provides improved base classes for regex-based parsers with
better error handling, performance optimization, and consistency.
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern

from codeconcat.base_types import Declaration, ParseResult

from .docstring_extractor import extract_docstring
from .error_handling import ErrorHandler
from .performance_optimizer import create_efficient_deduplicator, intern_string, performance_monitor
from .type_mapping import standardize_declaration_kind

logger = logging.getLogger(__name__)


@dataclass
class ParserConfig:
    """Configuration for enhanced parsers."""

    language: str
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_line_length: int = 10000
    enable_performance_monitoring: bool = True
    enable_string_interning: bool = True
    cache_patterns: bool = True
    batch_size: int = 100


class EnhancedBaseParser(ABC):
    """
    Enhanced base parser with improved functionality.

    This class provides a foundation for regex-based parsers with:
    - Better error handling and recovery
    - Performance optimization
    - Consistent output format
    - Security features
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the enhanced parser.

        Args:
            config: Parser configuration
        """
        self.config = config
        self.language = config.language
        self.error_handler = ErrorHandler(self.language)

        # Performance optimization
        self.deduplicator = create_efficient_deduplicator()

        # Pattern cache
        self._pattern_cache: Optional[Dict[str, Pattern]] = {} if config.cache_patterns else None

        # Initialize patterns
        self._init_patterns()

    @abstractmethod
    def _init_patterns(self) -> None:
        """Initialize language-specific patterns."""
        pass

    @abstractmethod
    def get_language_patterns(self) -> Dict[str, str]:
        """
        Get language-specific regex patterns.

        Returns:
            Dictionary of pattern names to regex strings
        """
        pass

    def _get_compiled_pattern(self, pattern_name: str) -> Optional[Pattern]:
        """
        Get a compiled pattern with caching.

        Args:
            pattern_name: Name of the pattern

        Returns:
            Compiled regex pattern or None if not found
        """
        if self._pattern_cache is None:
            # No caching enabled
            patterns = self.get_language_patterns()
            pattern_str = patterns.get(pattern_name)
            if pattern_str:
                return re.compile(pattern_str, re.MULTILINE)
            return None

        # Check cache first
        if pattern_name in self._pattern_cache:
            return self._pattern_cache[pattern_name]

        # Compile and cache
        patterns = self.get_language_patterns()
        pattern_str = patterns.get(pattern_name)
        if pattern_str:
            try:
                compiled = re.compile(pattern_str, re.MULTILINE)
                self._pattern_cache[pattern_name] = compiled
                return compiled
            except re.error as e:
                logger.error(f"Failed to compile pattern '{pattern_name}': {e}")
                return None

        return None

    @performance_monitor(f"{__name__}.parse")
    def parse(self, content: str, file_path: str) -> ParseResult:
        """
        Parse the content and extract declarations and imports.

        Args:
            content: The source content
            file_path: Path to the file being parsed

        Returns:
            ParseResult with extracted information
        """
        # Security: Check file size
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > self.config.max_file_size:
            return self.error_handler.handle_error(
                f"File too large: {len(content_bytes)} bytes (max: {self.config.max_file_size})",
                file_path,
                context={"file_size_bytes": len(content_bytes)},
            )

        # Security: Check for extremely long lines
        lines = content.split("\n")
        if any(len(line) > self.config.max_line_length for line in lines):
            return self.error_handler.handle_error(
                f"Line too long (>{self.config.max_line_length} characters)",
                file_path,
                context={"max_line_length": self.config.max_line_length},
            )

        try:
            # Extract imports
            imports = self._extract_imports(content, file_path)

            # Extract declarations
            declarations = self._extract_declarations(content, file_path)

            # Deduplicate and sort
            declarations = self.deduplicator(declarations)
            imports = self.deduplicator(imports)

            declarations.sort(key=lambda d: d.start_line)
            imports.sort()

            return self.error_handler.create_success_result(
                declarations,
                imports,
                file_path,
                context={"total_declarations": len(declarations), "total_imports": len(imports)},
            )

        except Exception as e:
            return self.error_handler.handle_error(
                f"Parse error: {e}", file_path, context={"exception_type": type(e).__name__}
            )

    def _extract_imports(self, content: str, _file_path: str) -> List[str]:
        """
        Extract import statements from content.

        Args:
            content: The source content
            file_path: Path to the file

        Returns:
            List of import statements
        """
        imports = []

        # Get import patterns
        import_patterns = [
            ("import_statement", self._get_compiled_pattern("import_statement")),
            ("from_import", self._get_compiled_pattern("from_import")),
            ("require", self._get_compiled_pattern("require")),
            ("include", self._get_compiled_pattern("include")),
        ]

        lines = content.split("\n")

        for pattern_name, pattern in import_patterns:
            if not pattern:
                continue

            for line_num, line in enumerate(lines, 1):
                try:
                    match = pattern.search(line)
                    if match:
                        import_text = match.group(0).strip()
                        if self.config.enable_string_interning:
                            import_text = intern_string(import_text)
                        imports.append(import_text)
                except Exception as e:
                    logger.debug(
                        f"Error matching import pattern {pattern_name} at line {line_num}: {e}"
                    )

        return imports

    def _extract_declarations(self, content: str, file_path: str) -> List[Declaration]:
        """
        Extract declarations from content.

        Args:
            content: The source content
            file_path: Path to the file

        Returns:
            List of declarations
        """
        declarations = []
        lines = content.split("\n")

        # Get declaration patterns
        declaration_patterns = self._get_declaration_patterns()

        for pattern_name, pattern in declaration_patterns.items():
            if not pattern:
                continue

            for line_num, line in enumerate(lines, 1):
                try:
                    match = pattern.search(line)
                    if match:
                        declaration = self._create_declaration_from_match(
                            match, pattern_name, line_num, content, file_path
                        )
                        if declaration:
                            declarations.append(declaration)
                except Exception as e:
                    logger.debug(
                        f"Error matching declaration pattern {pattern_name} at line {line_num}: {e}"
                    )

        return declarations

    def _get_declaration_patterns(self) -> Dict[str, Pattern]:
        """
        Get declaration patterns for the language.

        Returns:
            Dictionary of pattern names to compiled patterns
        """
        patterns = {}

        # Common declaration patterns
        common_patterns = {
            "function": self._get_compiled_pattern("function"),
            "class": self._get_compiled_pattern("class"),
            "interface": self._get_compiled_pattern("interface"),
            "struct": self._get_compiled_pattern("struct"),
            "enum": self._get_compiled_pattern("enum"),
            "variable": self._get_compiled_pattern("variable"),
            "constant": self._get_compiled_pattern("constant"),
            "method": self._get_compiled_pattern("method"),
            "property": self._get_compiled_pattern("property"),
        }

        # Filter out None patterns
        for name, pattern in common_patterns.items():
            if pattern is not None:
                patterns[name] = pattern

        return patterns

    def _create_declaration_from_match(
        self, match: re.Match, pattern_name: str, line_num: int, content: str, _file_path: str
    ) -> Optional[Declaration]:
        """
        Create a Declaration object from a regex match.

        Args:
            match: The regex match
            pattern_name: Name of the pattern that matched
            line_num: Line number where the match occurred
            content: Full source content
            file_path: Path to the file

        Returns:
            Declaration object or None if creation failed
        """
        try:
            # Extract name from match
            name = match.groupdict().get("name")
            if not name:
                name = match.group(1) if match.groups() else "unknown"

            # Standardize the kind
            standardized_kind = standardize_declaration_kind(self.language, pattern_name)

            # Extract docstring
            docstring = extract_docstring(content, self.language, line_num, line_num, name)

            # Extract signature if available
            signature = match.groupdict().get("signature", "")

            # Extract modifiers
            modifiers = set()
            for modifier_field in ["modifiers", "visibility", "access"]:
                modifier_value = match.groupdict().get(modifier_field)
                if modifier_value:
                    modifiers.add(modifier_value.strip())

            # Optimize strings if enabled
            if self.config.enable_string_interning:
                name = intern_string(name)
                docstring = intern_string(docstring)
                signature = intern_string(signature)
                modifiers = {intern_string(m) for m in modifiers}

            return Declaration(
                name=name,
                kind=standardized_kind,
                start_line=line_num,
                end_line=line_num,  # Basic parsers typically work line-by-line
                docstring=docstring,
                signature=signature,
                modifiers=modifiers,
            )

        except Exception as e:
            logger.debug(f"Error creating declaration from match: {e}")
            return None


class EnhancedCFamilyParser(EnhancedBaseParser):
    """
    Enhanced parser for C-family languages (C, C++, C#, Java).

    Provides common functionality for C-style languages with braces,
    semicolons, and similar syntax.
    """

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """
        Find the end of a block started at the given line.

        Args:
            lines: List of source lines
            start: Starting line index (0-based, typically the line with opening brace)

        Returns:
            Index of the line where the block ends
        """
        # Initialize to 1 since we're called after finding an opening brace
        brace_count = 1
        in_string = False
        in_char = False
        escape_next = False

        for i in range(start, len(lines)):
            line = lines[i]

            for char in line:
                if escape_next:
                    escape_next = False
                    continue

                if char == "\\":
                    escape_next = True
                    continue

                if in_string:
                    if char == '"':
                        in_string = False
                    continue

                if in_char:
                    if char == "'":
                        in_char = False
                    continue

                if char == '"':
                    in_string = True
                elif char == "'":
                    in_char = True
                elif char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count <= 0:
                        return i

        return len(lines) - 1


class EnhancedIndentationParser(EnhancedBaseParser):
    """
    Enhanced parser for indentation-based languages (Python).

    Provides functionality for languages that use indentation
    to define blocks rather than braces.
    """

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """
        Find the end of an indented block.

        Args:
            lines: List of source lines
            start: Starting line index (0-based)

        Returns:
            Index of the line where the block ends
        """
        if start >= len(lines):
            return len(lines) - 1

        # Get the indentation of the starting line
        start_indent = len(lines[start]) - len(lines[start].lstrip())

        for i in range(start + 1, len(lines)):
            line = lines[i]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Get current line indentation
            current_indent = len(line) - len(line.lstrip())

            # If indentation is less than or equal to start, block ended
            if current_indent <= start_indent:
                return i - 1

        return len(lines) - 1
