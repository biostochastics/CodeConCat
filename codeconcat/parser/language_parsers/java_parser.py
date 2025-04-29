import logging
import re
from typing import List, Set

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError
from .base_parser import BaseParser  # Import BaseParser

logger = logging.getLogger(__name__)


class JavaParser(BaseParser):
    """Parses Java code to extract declarations and imports using Regex."""

    def __init__(self):
        """Initializes the Java parser with regex patterns."""
        # Regex to find class, interface, enum, annotation, method declarations
        # Supports basic modifiers like public, private, protected, static, final, abstract
        # Captures type ('class', 'interface', 'enum', '@interface', method return type) and name
        # Adjusted method regex to better capture return type and name, handle generics
        self.declaration_pattern = re.compile(
            r"^\s*(?:(?:public|private|protected|static|final|abstract|synchronized|native|strictfp)\s+)*"
            r"(?:(?P<type>class|interface|enum|@interface)\s+(?P<name>[\w\$]+))"
            r"|(?:(?P<return_type>(?:[\w\.\$<>,\[\]?]+\s+)+?)(?P<method_name>[\w\$]+)\s*\([^)]*\))"
            # Potential issue: void methods might not be captured correctly if return_type requires trailing space.
            # Simplified method capture:
            # r"|(?:(?P<return_type>[\w\.<>\[\]\?]+(?:\s*\[\])?)\s+(?P<method_name>[\w\$]+)\s*\(.*\))" # Method signature
            # r"|(?:void\s+(?P<method_name_void>[\w\$]+)\s*\(.*\))" # void methods
        )
        # Regex to find import statements
        self.import_pattern = re.compile(r"^\s*import\s+(?:static\s+)?(?P<name>[\w\.\*]+);")

    # Update signature to match ParserInterface
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses the given Java code content.

        Args:
            content: The Java code as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object containing declarations and imports.
        """
        declarations = []
        imports: Set[str] = set()
        lines = content.split("\n")
        in_multiline_comment = False
        docstring_buffer: List[str] = []

        # Add error handling from the old parse_java function
        try:
            logger.debug(f"Starting JavaParser.parse for file: {file_path}")
            for i, line in enumerate(lines):
                stripped_line = line.strip()

                # Handle multi-line comments
                if in_multiline_comment:
                    if "*/" in stripped_line:
                        in_multiline_comment = False
                        stripped_line = stripped_line.split("*/", 1)[1].strip()
                    else:
                        continue  # Still inside comment
                if stripped_line.startswith("/*") and "*/" not in stripped_line:
                    in_multiline_comment = True
                    # Capture potential start of docstring
                    if stripped_line.startswith("/**"):
                        docstring_buffer = [stripped_line]
                    continue
                elif stripped_line.startswith("/**") and stripped_line.endswith("*/"):
                    # Single line doc comment /** ... */
                    docstring_buffer = [stripped_line]
                    # Clear buffer after processing potential declaration below
                elif stripped_line.startswith("//"):
                    continue  # Skip single line comments

                # Extract imports
                import_match = self.import_pattern.match(line)
                if import_match:
                    imports.add(import_match.group("name"))
                    docstring_buffer = []  # Reset docstring buffer on import
                    continue

                # Extract declarations
                declaration_match = self.declaration_pattern.match(line)
                if declaration_match:
                    kind = ""
                    name = ""
                    if declaration_match.group("type"):
                        kind = declaration_match.group("type")
                        name = declaration_match.group("name")
                    elif declaration_match.group("method_name"):
                        kind = "method"
                        # Use return type + method name for uniqueness, or just method name?
                        # Name could be just method_name for simplicity
                        name = declaration_match.group("method_name")
                        # name = f"{declaration_match.group('return_type').strip()} {declaration_match.group('method_name')}"
                    # elif declaration_match.group("method_name_void"):
                    #     kind = "method"
                    #     name = declaration_match.group("method_name_void")

                    if kind and name:
                        # Process docstring buffer
                        docstring = ""
                        if docstring_buffer and docstring_buffer[0].startswith("/**"):
                            if len(docstring_buffer) == 1:
                                # Single-line doc comment /** ... */
                                doc_content = docstring_buffer[0][3:-2].strip()
                            else:
                                # Multi-line /** ... */ (already stripped '/**')
                                doc_lines = [docstring_buffer[0][3:].strip()]
                                for doc_line in docstring_buffer[1:-1]:
                                    # Remove leading * if present
                                    cleaned_line = doc_line.strip()
                                    if cleaned_line.startswith("*"):
                                        cleaned_line = cleaned_line[1:].strip()
                                    doc_lines.append(cleaned_line)
                                # Add last line (stripped '*/')
                                last_line = docstring_buffer[-1].strip()
                                if last_line.endswith("*/"):
                                    last_line = last_line[:-2].strip()
                                    if last_line.startswith("*"):
                                        last_line = last_line[1:].strip()
                                    doc_lines.append(last_line)
                                doc_content = "\n".join(doc_lines).strip()
                            docstring = doc_content

                        # TODO: Find end_line accurately - for now, assume single line
                        declarations.append(
                            Declaration(
                                kind=kind,
                                name=name,
                                start_line=i,
                                end_line=i,  # Placeholder
                                docstring=docstring,
                                modifiers=set(),  # Modifiers not extracted currently
                            )
                        )
                    docstring_buffer = []  # Reset buffer after finding declaration
                elif stripped_line and not stripped_line.startswith("import "):
                    # If line is not empty, not a comment, not import, not declaration
                    # Reset docstring buffer as it doesn't precede a declaration
                    docstring_buffer = []
                elif stripped_line.startswith("/**") and "*/" in stripped_line:
                    # Clear buffer if it was a single-line doc comment not preceding decl
                    docstring_buffer = []

            logger.debug(
                f"Finished JavaParser.parse for file: {file_path}. Found {len(declarations)} declarations, {len(imports)} unique imports."
            )
            # Return ParseResult
            return ParseResult(
                file_path=file_path,
                language="java",
                content=content,
                declarations=declarations,
                imports=sorted(list(imports)),
                engine_used="regex",
            )

        except Exception as e:
            # Wrap internal parser errors
            logger.error(f"Error parsing Java file {file_path}: {e}", exc_info=True)
            raise LanguageParserError(
                message=f"Failed to parse Java file ({type(e).__name__}): {e}",
                file_path=file_path,
                original_exception=e,
            )
