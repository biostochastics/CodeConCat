"""
Improvements for standard regex-based parsers in the CodeConCat project.

This module provides enhancements to address the limitations of standard
regex-based parsers, including multi-line construct support, error recovery,
and improved pattern matching.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from re import Pattern

from codeconcat.base_types import Declaration, ParseResult

from .docstring_extractor import extract_docstring
from .error_handling import ErrorHandler
from .performance_optimizer import intern_string, performance_monitor
from .type_mapping import standardize_declaration_kind

logger = logging.getLogger(__name__)


class PatternMatchStrategy(Enum):
    """Strategies for pattern matching."""

    SINGLE_LINE = "single_line"
    MULTI_LINE = "multi_line"
    CONTEXT_AWARE = "context_aware"
    RECURSIVE = "recursive"


@dataclass
class MatchContext:
    """Context information for pattern matching."""

    line_number: int
    previous_line: str | None = None
    next_line: str | None = None
    indentation_level: int = 0
    in_string: bool = False
    in_comment: bool = False
    brace_depth: int = 0
    paren_depth: int = 0


class MultiLinePatternMatcher:
    """
    Enhanced pattern matcher for multi-line constructs.

    This class can handle patterns that span multiple lines,
    with proper context awareness and error recovery.
    """

    def __init__(self, max_lines: int = 50):
        """
        Initialize the multi-line pattern matcher.

        Args:
            max_lines: Maximum number of lines to consider for multi-line patterns
        """
        self.max_lines = max_lines
        self._compiled_patterns: dict[str, Pattern] = {}

    def add_pattern(self, name: str, pattern: str, flags: int = re.MULTILINE) -> None:
        """
        Add a multi-line pattern.

        Args:
            name: Pattern name
            pattern: Regex pattern
            flags: Regex flags
        """
        try:
            self._compiled_patterns[name] = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"Failed to compile pattern '{name}': {e}")

    def match_multi_line(
        self,
        lines: list[str],
        start_line: int,
        pattern_name: str,
        _context: MatchContext | None = None,
    ) -> re.Match | None:
        """
        Match a multi-line pattern starting at the given line.

        Args:
            lines: List of source lines
            start_line: Starting line index (0-based)
            pattern_name: Name of the pattern to match
            context: Optional match context

        Returns:
            Match object or None if no match
        """
        if pattern_name not in self._compiled_patterns:
            return None

        pattern = self._compiled_patterns[pattern_name]

        # Determine the range of lines to consider
        end_line = min(start_line + self.max_lines, len(lines))

        # Join the lines for matching
        text = "\n".join(lines[start_line:end_line])

        try:
            return pattern.search(text)
        except re.error as e:
            logger.debug(f"Error matching pattern '{pattern_name}': {e}")
            return None


class ErrorRecoveryParser:
    """
    Parser with error recovery capabilities.

    This parser can continue parsing even when encountering
    syntax errors or malformed input.
    """

    def __init__(self, language: str):
        """
        Initialize the error recovery parser.

        Args:
            language: Programming language
        """
        self.language = language
        self.error_handler = ErrorHandler(language)
        self._recovery_strategies = self._init_recovery_strategies()

    def _init_recovery_strategies(self) -> dict[str, Callable]:
        """
        Initialize error recovery strategies.

        Returns:
            Dictionary of strategy names to functions
        """
        return {
            "skip_to_next_declaration": self._skip_to_next_declaration,
            "skip_to_next_line": self._skip_to_next_line,
            "skip_to_matching_brace": self._skip_to_matching_brace,
            "skip_to_matching_indent": self._skip_to_matching_indent,
        }

    def _skip_to_next_declaration(
        self, lines: list[str], current_line: int, patterns: dict[str, Pattern]
    ) -> int:
        """
        Skip to the next declaration line.

        Args:
            lines: List of source lines
            current_line: Current line index
            patterns: Declaration patterns to match

        Returns:
            Index of the next declaration line
        """
        for i in range(current_line + 1, len(lines)):
            line = lines[i]

            # Check if this line matches any declaration pattern
            for pattern in patterns.values():
                if pattern.search(line):
                    return i

        return len(lines) - 1

    def _skip_to_next_line(self, lines: list[str], current_line: int) -> int:
        """
        Skip to the next line.

        Args:
            lines: List of source lines
            current_line: Current line index

        Returns:
            Index of the next line
        """
        return min(current_line + 1, len(lines) - 1)

    def _skip_to_matching_brace(self, lines: list[str], current_line: int) -> int:
        """
        Skip to the line with a matching closing brace.

        Args:
            lines: List of source lines
            current_line: Current line index

        Returns:
            Index of the line with matching brace
        """
        brace_count = 0

        for i in range(current_line, len(lines)):
            line = lines[i]

            for char in line:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return i

        return len(lines) - 1

    def _skip_to_matching_indent(self, lines: list[str], current_line: int) -> int:
        """
        Skip to the line with matching indentation.

        Args:
            lines: List of source lines
            current_line: Current line index

        Returns:
            Index of the line with matching indentation
        """
        if current_line >= len(lines):
            return len(lines) - 1

        # Get the indentation of the current line
        current_indent = len(lines[current_line]) - len(lines[current_line].lstrip())

        for i in range(current_line + 1, len(lines)):
            line = lines[i]

            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Get current line indentation
            line_indent = len(line) - len(line.lstrip())

            # If indentation is less than or equal to current, return
            if line_indent <= current_indent:
                return i - 1

        return len(lines) - 1


class ContextAwareParser:
    """
    Parser with context awareness for better pattern matching.

    This parser considers the surrounding context when matching
    patterns, improving accuracy for complex constructs.
    """

    def __init__(self, language: str):
        """
        Initialize the context-aware parser.

        Args:
            language: Programming language
        """
        self.language = language
        self.error_handler = ErrorHandler(language)

    def _build_context(self, lines: list[str], line_index: int) -> MatchContext:
        """
        Build context information for a line.

        Args:
            lines: List of source lines
            line_index: Index of the current line

        Returns:
            MatchContext object
        """
        line = lines[line_index]

        # Get previous and next lines
        prev_line = lines[line_index - 1] if line_index > 0 else None
        next_line = lines[line_index + 1] if line_index < len(lines) - 1 else None

        # Calculate indentation level
        indent_level = len(line) - len(line.lstrip())

        # Check if we're in a string or comment
        in_string = False
        in_comment = False

        # Simple check for string/comment state
        # In a more sophisticated implementation, we would track this across lines
        stripped = line.strip()
        if stripped.startswith(('"""', "'''", '"', "'")):
            in_string = True
        elif stripped.startswith(("#", "//", "/*")):
            in_comment = True

        # Calculate brace and parenthesis depth
        brace_depth = line.count("{") - line.count("}")
        paren_depth = line.count("(") - line.count(")")

        return MatchContext(
            line_number=line_index + 1,
            previous_line=prev_line,
            next_line=next_line,
            indentation_level=indent_level,
            in_string=in_string,
            in_comment=in_comment,
            brace_depth=brace_depth,
            paren_depth=paren_depth,
        )

    def _should_skip_pattern(self, pattern_name: str, context: MatchContext) -> bool:
        """
        Check if a pattern should be skipped based on context.

        Args:
            pattern_name: Name of the pattern
            context: Match context

        Returns:
            True if the pattern should be skipped
        """
        # Skip if we're in a comment
        if context.in_comment:
            return True

        # Skip if we're in a string (for most patterns)
        if context.in_string and pattern_name not in ["string_literal", "docstring"]:
            return True

        # Language-specific rules
        if self.language == "python":
            # Skip if indentation level is too deep (might be in a nested function)
            if context.indentation_level > 20 and pattern_name in ["class", "function"]:
                return True
        elif (
            self.language in ["c", "cpp", "java", "csharp"]
            and context.brace_depth > 10
            and pattern_name in ["class", "function", "struct"]
        ):
            # Skip if we're deep in nested braces
            return True

        return False


class ImprovedStandardParser:
    """
    Improved standard parser with enhanced capabilities.

    This parser addresses the limitations of basic regex-based parsers
    by adding multi-line support, error recovery, and context awareness.
    """

    def __init__(self, language: str):
        """
        Initialize the improved standard parser.

        Args:
            language: Programming language
        """
        self.language = language
        self.error_handler = ErrorHandler(language)

        # Initialize components
        self.multi_line_matcher = MultiLinePatternMatcher()
        self.error_recovery = ErrorRecoveryParser(language)
        self.context_parser = ContextAwareParser(language)

        # Initialize patterns
        self._init_patterns()

    def _init_patterns(self) -> None:
        """Initialize language-specific patterns."""
        # This should be overridden by subclasses
        pass

    @performance_monitor(f"{__name__}.parse")
    def parse(self, content: str, file_path: str) -> ParseResult:
        """
        Parse the content with enhanced capabilities.

        Args:
            content: The source content
            file_path: Path to the file

        Returns:
            ParseResult with extracted information
        """
        lines = content.split("\n")
        declarations = []
        imports = []

        try:
            # Extract imports
            imports = self._extract_imports_enhanced(lines, file_path)

            # Extract declarations with error recovery
            declarations = self._extract_declarations_enhanced(lines, file_path)

            # Sort and deduplicate
            declarations.sort(key=lambda d: d.start_line)
            imports = sorted(set(imports))

            return self.error_handler.create_success_result(declarations, imports, file_path)

        except Exception as e:
            return self.error_handler.handle_error(
                f"Parse error: {e}", file_path, context={"exception_type": type(e).__name__}
            )

    def _extract_imports_enhanced(self, lines: list[str], _file_path: str) -> list[str]:
        """
        Extract imports with enhanced pattern matching.

        Args:
            lines: List of source lines
            file_path: Path to the file

        Returns:
            List of import statements
        """
        imports = []

        # Get import patterns
        import_patterns = self._get_import_patterns()

        for line_num, line in enumerate(lines):
            context = self.context_parser._build_context(lines, line_num)

            # Skip if context indicates we should
            if self.context_parser._should_skip_pattern("import", context):
                continue

            # Try each pattern
            for _pattern_name, pattern in import_patterns.items():
                if pattern.search(line):
                    import_text = line.strip()
                    imports.append(import_text)
                    break

        return imports

    def _extract_declarations_enhanced(self, lines: list[str], file_path: str) -> list[Declaration]:
        """
        Extract declarations with enhanced pattern matching and error recovery.

        Args:
            lines: List of source lines
            file_path: Path to the file

        Returns:
            List of declarations
        """
        declarations = []

        # Get declaration patterns
        declaration_patterns = self._get_declaration_patterns()

        line_num = 0
        while line_num < len(lines):
            line = lines[line_num]
            context = self.context_parser._build_context(lines, line_num)

            # Skip if context indicates we should
            should_skip = True
            for pattern_name in declaration_patterns:
                if not self.context_parser._should_skip_pattern(pattern_name, context):
                    should_skip = False
                    break

            if should_skip:
                line_num += 1
                continue

            # Try to match patterns
            matched = False
            for pattern_name, pattern in declaration_patterns.items():
                match = pattern.search(line)
                if match:
                    try:
                        declaration = self._create_declaration_from_match_enhanced(
                            match, pattern_name, line_num, lines, file_path, context
                        )
                        if declaration:
                            declarations.append(declaration)
                            matched = True
                            break
                    except Exception as e:
                        logger.debug(f"Error creating declaration: {e}")
                        # Continue with error recovery
                        continue

            if not matched:
                # Try error recovery
                line_num = self.error_recovery._recovery_strategies["skip_to_next_declaration"](
                    lines, line_num, declaration_patterns
                )

            line_num += 1

        return declarations

    def _get_import_patterns(self) -> dict[str, Pattern]:
        """
        Get import patterns for the language.

        Returns:
            Dictionary of pattern names to compiled patterns

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError("Subclasses must implement _get_import_patterns()")

    def _get_declaration_patterns(self) -> dict[str, Pattern]:
        """
        Get declaration patterns for the language.

        Returns:
            Dictionary of pattern names to compiled patterns

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError("Subclasses must implement _get_declaration_patterns()")

    def _create_declaration_from_match_enhanced(
        self,
        match: re.Match,
        pattern_name: str,
        line_num: int,
        lines: list[str],
        _file_path: str,
        context: MatchContext,
    ) -> Declaration | None:
        """
        Create a Declaration object from a regex match with enhanced context.

        Args:
            match: The regex match
            pattern_name: Name of the pattern that matched
            line_num: Line number where the match occurred
            lines: List of all source lines
            file_path: Path to the file
            context: Match context

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

            # Extract docstring with context awareness
            content = "\n".join(lines)
            docstring = extract_docstring(content, self.language, line_num + 1, line_num + 1, name)

            # Extract signature if available
            signature = match.groupdict().get("signature", "")

            # Extract modifiers with context
            modifiers = self._extract_modifiers_enhanced(match, context)

            # Optimize strings
            name = intern_string(name)
            docstring = intern_string(docstring)
            signature = intern_string(signature)
            modifiers = {intern_string(m) for m in modifiers}

            return Declaration(
                name=name,
                kind=standardized_kind,
                start_line=line_num + 1,
                end_line=line_num + 1,
                docstring=docstring,
                signature=signature,
                modifiers=modifiers,
            )

        except Exception as e:
            logger.debug(f"Error creating declaration from match: {e}")
            return None

    def _extract_modifiers_enhanced(self, match: re.Match, context: MatchContext) -> set[str]:
        """
        Extract modifiers with enhanced context awareness.

        Args:
            match: The regex match
            context: Match context

        Returns:
            Set of modifier strings
        """
        modifiers = set()

        # Extract from match groups
        for modifier_field in ["modifiers", "visibility", "access"]:
            modifier_value = match.groupdict().get(modifier_field)
            if modifier_value:
                modifiers.add(modifier_value.strip())

        # Add context-based modifiers
        if context.brace_depth > 0:
            modifiers.add("nested")

        if context.indentation_level > 0:
            modifiers.add("indented")

        return modifiers
