"""C# code parser for CodeConcat."""

import logging
import re
from typing import List, Set

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# Simple Regex patterns for C# constructs (can be improved)
# Note: Regex is limited for complex C# syntax (generics, attributes, etc.)
NAMESPACE_PATTERN = re.compile(r"^\s*namespace\s+([\w\.]+)")
USING_PATTERN = re.compile(r"^\s*using\s+([\w\.]+);")
CLASS_INTERFACE_ENUM_PATTERN = re.compile(
    r"^\s*(?:public|private|protected|internal|static|abstract|sealed)?\s*"
    r"(?:partial\s+)?"
    r"(?P<kind>class|interface|struct|enum)\s+(?P<name>[\w<>\?,\s]+)"
    # Handle inheritance, interfaces, constraints : ...
    r"(?:\s*:\s*[\w\.<>\?,\s]+)?\s*\{?"
)
METHOD_CONSTRUCTOR_PATTERN = re.compile(
    r"^\s*(?:public|private|protected|internal|static|virtual|override|abstract|async|unsafe)?\s*"
    # Return type or constructor name
    r"(?:[\w\.<>\[\]\?]+\s+)?"
    # Method/Constructor name
    r"(?P<name>[\w~<>]+)"
    # Parameters
    r"\s*\(.*\)"
    # Constraints or body start
    r"(?:\s*where\s.*)?\s*\{?"
)
PROPERTY_FIELD_PATTERN = re.compile(
    r"^\s*(?:public|private|protected|internal|static|readonly|const|volatile)?\s*"
    # Type
    r"[\w\.<>\[\]\?]+\s+"
    # Name
    r"(?P<name>\w+)"
    # Body start, getter/setter, or semicolon
    r"\s*(?:\{|;|=>|=)"
)
DOC_COMMENT_PATTERN = re.compile(r"^\s*///\s?(.*)")


# Inherit from BaseParser
class CSharpParser(BaseParser):
    """Parses C# code using Regex."""

    # Update signature to match ParserInterface
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses the given C# code content.

        Args:
            content: The C# code as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object containing declarations and imports (usings).
        """
        declarations = []
        imports: Set[str] = set()  # Using directives
        lines = content.split("\n")
        doc_buffer: List[str] = []
        in_multiline_comment = False

        try:
            logger.debug(f"Starting CSharpParser.parse (Regex) for file: {file_path}")
            for i, line in enumerate(lines):
                stripped_line = line.strip()

                # Handle block comments /* ... */
                if in_multiline_comment:
                    if "*/" in stripped_line:
                        in_multiline_comment = False
                        stripped_line = stripped_line.split("*/", 1)[1].strip()
                    else:
                        continue
                if stripped_line.startswith("/*") and "*/" not in stripped_line:
                    in_multiline_comment = True
                    doc_buffer = []  # Block comments clear doc buffer
                    continue
                elif stripped_line.startswith("//") and not stripped_line.startswith("///"):
                    doc_buffer = []  # Regular line comments clear doc buffer
                    continue  # Skip regular comments

                # Handle doc comments ///
                doc_match = DOC_COMMENT_PATTERN.match(line)
                if doc_match:
                    # Allow multi-line doc comments by checking previous line
                    if i > 0 and DOC_COMMENT_PATTERN.match(lines[i - 1].strip()):
                        doc_buffer.append(doc_match.group(1))
                    else:
                        doc_buffer = [doc_match.group(1)]  # Start new buffer
                    continue  # Don't process doc comment lines further

                # Using directives (Imports)
                using_match = USING_PATTERN.match(stripped_line)
                if using_match:
                    imports.add(using_match.group(1))
                    doc_buffer = []  # Clear doc buffer after using
                    continue

                # Namespace
                namespace_match = NAMESPACE_PATTERN.match(stripped_line)
                if namespace_match:
                    namespace_match.group(1)
                    # Optionally prepend namespace to subsequent declarations?
                    doc_buffer = []
                    continue

                # Class/Interface/Struct/Enum
                cie_match = CLASS_INTERFACE_ENUM_PATTERN.match(stripped_line)
                if cie_match:
                    kind = cie_match.group("kind")
                    name = cie_match.group("name").strip()  # Clean up potential generics noise
                    # Remove generics part for simpler name matching if needed
                    # name = re.sub(r'<.*>', '', name)
                    docstring = self._format_docstring(doc_buffer)
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )  # Placeholder end_line
                    doc_buffer = []
                    continue

                # Method/Constructor
                mc_match = METHOD_CONSTRUCTOR_PATTERN.match(stripped_line)
                if mc_match:
                    name = mc_match.group("name")
                    kind = (
                        "method"
                        if name and not name.startswith("~") and "." not in name
                        else "constructor"
                    )  # Basic heuristic
                    # Heuristic to exclude explicit interface implementations for now
                    if "." in name:
                        continue
                    docstring = self._format_docstring(doc_buffer)
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )  # Placeholder end_line
                    doc_buffer = []
                    continue

                # Property/Field (Basic)
                pf_match = PROPERTY_FIELD_PATTERN.match(stripped_line)
                if pf_match:
                    name = pf_match.group("name")
                    kind = "property/field"  # Cannot easily distinguish with simple regex
                    docstring = self._format_docstring(doc_buffer)
                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=i,
                            end_line=i,
                            docstring=docstring,
                            modifiers=set(),
                        )
                    )  # Placeholder end_line
                    doc_buffer = []
                    continue

                # If line wasn't comment, import, or declaration, clear doc buffer
                if stripped_line:
                    doc_buffer = []

            logger.debug(
                f"Finished CSharpParser.parse (Regex) for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} usings."
            )
            return ParseResult(
                file_path=file_path,
                language="csharp",
                content=content,
                declarations=declarations,
                imports=sorted(imports),  # Usings are treated as imports
                engine_used="regex",
                token_stats=None,
                security_issues=[],
            )

        except Exception as e:
            logger.error(f"Error parsing C# file {file_path} with Regex: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse C# file ({type(e).__name__}) using Regex: {e}",
                file_path=file_path,
                original_exception=e,
            ) from e

    def _format_docstring(self, doc_buffer: List[str]) -> str:
        """Formats the collected /// comments, potentially stripping XML tags."""
        # Basic implementation: join lines. Could add XML stripping later.
        return "\n".join(doc_buffer).strip()
