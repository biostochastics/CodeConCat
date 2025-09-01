"""JavaScript/TypeScript code parser for CodeConcat."""

import logging
import re
from typing import List, Set

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class JsTsParser(BaseParser):
    """Parses JavaScript/TypeScript code using simple Regex patterns."""

    def __init__(self):
        """Initialize JS/TS parser with regex patterns."""
        # Simpler patterns focusing on common declaration keywords
        self.declaration_pattern = re.compile(
            r"^\s*(?:export\s+)?(?:async\s+)?"
            # const foo = function() | const foo = async () => | class Foo | new class
            r"(?:(?:const|let|var)\s+(?P<name_var>[\w\$]+)\s*=\s*(?:function\*?|async\s*function\*?|\([^)]*\)\s*=>|class\b|new\s+class\b))"
            # function foo() | async function foo()
            r"|(?:function\*?\s+(?P<name_func>[\w\$]+))"
            # class Foo
            r"|(?:class\s+(?P<name_class>[\w\$]+))"
            # interface IFoo | type TBar (TypeScript)
            r"|(?:(?:export\s+)?(?:interface|type)\s+(?P<name_type>[\w\$]+))"
        )
        # Pattern for imports (import ... from ..., import ..., require)
        self.import_pattern = re.compile(
            # import ... from 'path'; (handles various forms inside)
            r"^\s*import(?:\s+.*\s+from)?\s+['\"](?P<from_path>[^'\"]+)['\"];?"
            # import('path'); (dynamic import)
            r"|\bimport\(['\"](?P<import_path>[^'\"]+)['\"]\);?"
            # require('path');
            r"|\brequire\(['\"](?P<require_path>[^'\"]+)['\"]\);?"
        )
        self.doc_comment_start_pattern = re.compile(r"^\s*/\*\*.*")
        self.doc_comment_end_pattern = re.compile(r".*\*/\s*$")
        self.multi_line_comment_start_pattern = re.compile(r"^\s*/\*.*")
        self.multi_line_comment_end_pattern = re.compile(r".*\*/\s*$")
        self.single_line_comment_pattern = re.compile(r"^\s*//.*")

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses the given JS/TS code content using simple regex.

        Args:
            content: The JS/TS code as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object containing declarations and imports.
        """
        declarations = []
        imports: Set[str] = set()
        lines = content.split("\n")
        in_multiline_comment = False
        docstring_buffer: List[str] = []

        try:
            logger.debug(f"Starting JsTsParser.parse (Regex) for file: {file_path}")
            for i, line in enumerate(lines):
                original_line = line  # Keep original for context if needed
                stripped_line = line.strip()
                current_line_docstring = None

                # --- Comment Handling --- #
                if in_multiline_comment:
                    if self.multi_line_comment_end_pattern.search(line):
                        in_multiline_comment = False
                        # Process potential remaining part of the line after comment ends
                        line_after_comment = line.split("*/", 1)[1]
                        stripped_line = line_after_comment.strip()
                        if not stripped_line:
                            continue  # Line was just the end of the comment
                    else:
                        # Still inside the comment block, add to buffer if it's a doc comment
                        if docstring_buffer:
                            docstring_buffer.append(line)
                        continue  # Skip the rest of the processing for this line

                # Check for start of multi-line comments (including doc comments)
                if self.multi_line_comment_start_pattern.search(line):
                    is_doc_comment = self.doc_comment_start_pattern.search(line)
                    # Check if it's also a single-line comment (e.g., /* ... */)
                    if self.multi_line_comment_end_pattern.search(line):
                        if is_doc_comment:
                            # Single-line doc comment - store it for potential use by next non-comment line
                            current_line_docstring = stripped_line
                        continue  # Skip processing rest of line
                    else:
                        # Start of a multi-line comment block
                        in_multiline_comment = True
                        if is_doc_comment:
                            docstring_buffer = [line]
                        continue  # Skip processing rest of line

                # Check for single-line comments
                if self.single_line_comment_pattern.match(stripped_line):
                    continue

                # --- Import Extraction --- #
                # (Run before declaration check as imports don't typically have docstrings attached)
                for match in self.import_pattern.finditer(
                    original_line
                ):  # Use original line for regex accuracy
                    path = next((p for p in match.groups() if p is not None), None)
                    if path:
                        imports.add(path)

                # --- Declaration Extraction --- #
                declaration_match = self.declaration_pattern.match(stripped_line)
                if declaration_match:
                    name = next((n for n in declaration_match.groups() if n is not None), None)
                    if name:
                        kind = "unknown"
                        if declaration_match.group("name_var"):
                            kind = "variable/function/class assignment"
                        elif declaration_match.group("name_func"):
                            kind = "function"
                        elif declaration_match.group("name_class"):
                            kind = "class"
                        elif declaration_match.group("name_type"):
                            kind = declaration_match.group(0).split()[1]  # interface or type

                        # Process collected docstring buffer or single-line docstring
                        docstring = ""
                        if docstring_buffer:
                            docstring = self._clean_jsdoc(docstring_buffer)
                        elif current_line_docstring:
                            docstring = self._clean_jsdoc([current_line_docstring])

                        declarations.append(
                            Declaration(
                                kind=kind,
                                name=name,
                                start_line=i,  # 0-indexed
                                end_line=i,  # Placeholder: Regex doesn't easily find block ends
                                docstring=docstring,
                                modifiers=set(),  # Modifiers not extracted by this simple regex
                            )
                        )
                        # Clear docstring buffer after associating with a declaration
                        docstring_buffer = []
                        current_line_docstring = None
                    else:
                        # No name found, maybe an anonymous function/class assignment without capture? Reset doc buffer.
                        docstring_buffer = []
                        current_line_docstring = None

                # --- Docstring Buffer Reset --- #
                # If the line was not empty, not a comment start/part, not a declaration,
                # and not an import line (imports handled separately), clear any pending docstring.
                elif stripped_line and not self.import_pattern.search(original_line):
                    docstring_buffer = []
                    current_line_docstring = None

            # Determine language based on file extension for the result
            language = "typescript" if file_path.lower().endswith((".ts", ".tsx")) else "javascript"
            logger.debug(
                f"Finished JsTsParser.parse (Regex) for {file_path} ({language}). Found {len(declarations)} declarations, {len(imports)} unique imports."
            )
            return ParseResult(
                file_path=file_path,
                language=language,
                content=content,
                declarations=declarations,
                imports=sorted(imports),
                engine_used="regex",  # Indicate regex engine was used
                token_stats=None,  # Regex parsers don't provide token stats
                security_issues=[],  # Regex parsers don't provide security issues
            )

        except Exception as e:
            # Wrap internal parser errors
            logger.error(f"Error parsing JS/TS file {file_path} with Regex: {e}", exc_info=True)
            language = "typescript" if file_path.lower().endswith((".ts", ".tsx")) else "javascript"
            raise LanguageParserError(
                message=f"Failed to parse {language} file ({type(e).__name__}) using Regex: {e}",
                file_path=file_path,
                original_exception=e,
            ) from e

    def _clean_jsdoc(self, docstring_lines: List[str]) -> str:
        """Cleans a JSDoc block comment buffer, removing delimiters and leading asterisks."""
        if not docstring_lines:
            return ""

        cleaned_lines: list[str] = []
        for i, line in enumerate(docstring_lines):
            stripped = line.strip()
            # Handle first line: remove /**
            if i == 0 and stripped.startswith("/**"):
                cleaned = stripped[3:].strip()
            # Handle last line: remove */
            elif i == len(docstring_lines) - 1 and stripped.endswith("*/"):
                cleaned = stripped[:-2].strip()
                # Remove potential leading * on the last line after */ removal
                if cleaned.startswith("*"):
                    cleaned = cleaned[1:].strip()
            # Handle intermediate lines: remove leading *
            elif stripped.startswith("*"):
                cleaned = stripped[1:].strip()
            # Handle lines that might not start with * (should be rare in valid JSDoc but handle defensively)
            else:
                cleaned = stripped

            # Only add non-empty lines after cleaning
            if cleaned:
                cleaned_lines.append(cleaned)

        return "\n".join(cleaned_lines)
